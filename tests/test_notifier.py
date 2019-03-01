import os
import airbrake
import mock
import platform
import socket
import unittest
import json
import sys
import traceback
import logging

from airbrake.notifier import Airbrake, capture
from airbrake.notice import Error, format_backtrace, ErrorLevels
from airbrake.utils import pytb_lastline
from airbrake.__about__ import __version__, __notifier__, __url__


class TestAirbrakeNotifier(unittest.TestCase):
    maxDiff = None

    def _create_notify(test, exception, session={},
                       environment={}, context={}, **params):
        def notify(self, notice):
            payload = notice.payload
            # print "payload %s" % payload
            if session:
                test.assertEqual(session, payload['session'])
            if environment:
                test.assertEqual(environment, payload['environment'])
            test.assertEqual(str(exception), payload['errors'][0]['message'])
            test.assertEqual(ErrorLevels.DEFAULT_LEVEL,
                             payload['context']['severity'])
            if context:
                test.assertEqual(context, payload['context'])
            for param_name, expected_value in params.items():
                test.assertEqual(expected_value,
                                 str(payload['params'][param_name]))
        return notify

    def setUp(self):
        super(TestAirbrakeNotifier, self).setUp()
        self.logger = airbrake.getLogger(
            'test-notifier',
            api_key='fakekey',
            project_id='fakeprojectid')
        self.session = {'user_id': 100}
        self.environment = {'PATH': '/usr/bin/'}
        self.context = {'hostname': socket.gethostname(),
                        'os': platform.platform(),
                        'language': 'Python/%s' % platform.python_version(),
                        'notifier': __notifier__,
                        'rootDirectory': os.getcwd(),
                        'severity': ErrorLevels.DEFAULT_LEVEL}

    def test_string(self):
        msg = "Zlonk!"
        notify = self._create_notify(msg)
        with mock.patch.object(Airbrake, 'notify', notify):
            try:
                raise Exception(msg)
            except:
                self.logger.exception(msg)

    def test_exception(self):
        msg = "Pow!"
        exception = Exception(msg)
        notify = self._create_notify(exception)
        with mock.patch.object(Airbrake, 'notify', notify):
            try:
                raise exception
            except Exception as e:
                self.logger.exception(e)

    def test_exception_with_session(self):
        msg = "Boff!"
        notify = self._create_notify(msg, session=self.session)
        with mock.patch.object(Airbrake, 'notify', notify):
            extra = {'session': self.session}
            try:
                raise Exception(msg)
            except Exception as e:
                self.logger.exception(e, extra=extra)

    def test_exception_with_environment(self):
        msg = "Whap!"
        notify = self._create_notify(msg, environment=self.environment)
        with mock.patch.object(Airbrake, 'notify', notify):
            extra = {'environment': self.environment}
            try:
                raise Exception(msg)
            except Exception as e:
                self.logger.exception(e, extra=extra)

    def test_exception_with_context(self):
        msg = "Zonk!"
        notify = self._create_notify(msg, context=self.context)
        with mock.patch.object(Airbrake, 'notify', notify):
            try:
                raise Exception(msg)
            except Exception as e:
                self.logger.exception(e)

    def test_exception_with_non_serializable(self):
        msg = "Narf!"

        class NonSerializable:
            def __repr__(self):
                return '<Use this instead>'
        non_serializable = NonSerializable()

        notify = self._create_notify(msg,
                                     very='important',
                                     jsonify=repr(non_serializable))
        with mock.patch.object(Airbrake, 'notify', notify, 'jsonify'):
            extra = {'very': 'important', 'jsonify': non_serializable}
            try:
                raise Exception(msg)
            except Exception as e:
                self.logger.exception(e, extra=extra)

    def test_notify_context(self):
        with mock.patch('requests.post') as requests_post:
            version = platform.python_version()
            plat = platform.platform()
            environment = u"testing123"
            root_directory = u"/home/app/"

            ab = Airbrake(project_id=1234, api_key='fake',
                          environment=environment,
                          root_directory=root_directory)
            ab.log("this is a test")

            expected_context = {
                u'notifier': {
                    u'name': u'airbrake-python',
                    u'version': __version__,
                    u'url': __url__
                },
                u'os': plat,
                u'hostname': socket.gethostname(),
                u'language': u'Python/%s' % version,
                u'environment': environment,
                u'rootDirectory': root_directory,
                u'severity': ErrorLevels.DEFAULT_LEVEL,
            }

            data = json.loads(requests_post.call_args[1]['data'])
            actual_context = data["context"]

            self.assertEqual(expected_context, actual_context)

    def test_log_with_severity(self):
        with mock.patch('requests.post') as requests_post:
            ab = Airbrake(project_id=1234, api_key='fake')
            ab.log("this is a test", severity=ErrorLevels.CRITICAL)

            data = json.loads(requests_post.call_args[1]['data'])
            actual_context = data["context"]

            self.assertEqual(actual_context[u'severity'], ErrorLevels.CRITICAL)

    def get_expected_payload(self, message, error_type):
        ctx = {
            'notifier': {
                'name': 'airbrake-python',
                'version': __version__,
                'url': __url__
            },
            'os': platform.platform(),
            'hostname': socket.gethostname(),
            'language': 'Python/%s' % platform.python_version(),
            'rootDirectory': os.getcwd(),
            'severity': ErrorLevels.DEFAULT_LEVEL
        }

        return {
            'errors': [{'backtrace': [{'function': 'N/A',
                                       'line': 1,
                                       'file': 'N/A'}],
                        'message': message,
                        'type': error_type}],
            'context': ctx,
            'notifier': {
                'url': 'https://github.com/airbrake/airbrake-python',
                'version': __version__,
                'name': 'airbrake-python'}
        }

    def test_capture(self):
        ab = Airbrake(project_id=1234, api_key='fake')

        try:
            raise ValueError("oh nos")
        except Exception:
            with mock.patch('requests.post') as requests_post:
                ab.capture()

                exc_info = sys.exc_info()
                raw_frames = traceback.extract_tb(exc_info[2])
                exc_frame = raw_frames[0]
                exception_str = exc_frame[3]
                exception_type = "ERROR:%s" % exc_frame[0]

                expected_payload = self.get_expected_payload(exception_str,
                                                             exception_type)

                data = {
                    'type': exc_info[1].__class__.__name__,
                    'backtrace': format_backtrace(exc_info[2]),
                    'message': str(exc_frame[3])
                }

                expected_payload['errors'] = [data]
                expected_payload['context']['severity'] =\
                    ErrorLevels.DEFAULT_LEVEL

                err = Error(exc_info=exc_info,
                            filename=str(exc_frame[0]),
                            line=str(exc_frame[1]),
                            function=str(exc_frame[2]),
                            message=str(exc_frame[3]),
                            errtype="ERROR:%s" % str(exc_frame[0]))
                notice = ab.build_notice(err)
                self.assertEqual(expected_payload, notice.payload)

                data = json.loads(requests_post.call_args[1]['data'])
                self.assertEqual(expected_payload, data)

    def test_capture_decorator(self):
        ab = Airbrake(project_id=1234, api_key='fake')

        with mock.patch('requests.post') as requests_post:

            @capture(ab)
            def faulty_func(msg):
                raise ValueError(msg)

            msg = "I am a banana"
            with self.assertRaises(ValueError) as cm:
                faulty_func(msg)
            self.assertEqual(msg, str(cm.exception))

            data = json.loads(requests_post.call_args[1]['data'])
            err_data = data['errors'][0]
            self.assertEqual(err_data['backtrace'][0]['function'],
                             'faulty_func')
            filename = err_data['backtrace'][0]['file']
            self.assertTrue(filename.endswith("tests/test_notifier.py"))

    def test_notify_str(self):
        ab = Airbrake(project_id=1234, api_key='fake')
        exception_str = "This is a test"
        exception_type = 'Error'
        notice = ab.build_notice(exception_str)

        expected_payload = self.get_expected_payload(exception_str,
                                                     exception_type)
        self.assertEqual(expected_payload, notice.payload)

        with mock.patch('requests.post') as requests_post:
            ab.notify(exception_str)
            data = json.loads(requests_post.call_args[1]['data'])
            self.assertEqual(expected_payload, data)

    def test_notify_exception(self):
        ab = Airbrake(project_id=1234, api_key='fake')
        exception_str = "This is a test"
        exception = ValueError(exception_str)
        exception_type = type(exception).__name__
        notice = ab.build_notice(exception)

        expected_payload = self.get_expected_payload(exception_str,
                                                     exception_type)

        self.assertEqual(expected_payload, notice.payload)

        with mock.patch('requests.post') as requests_post:
            ab.notify(exception)
            data = json.loads(requests_post.call_args[1]['data'])
            self.assertEqual(expected_payload, data)

    def test_notify_error(self):
        ab = Airbrake(project_id=1234, api_key='fake')

        try:
            raise TypeError
        except Exception as e:
            exc_info = sys.exc_info()
            error = Error(exc_info=exc_info)
            user = {
                "id": "12345",
                "name": "root",
                "email": "root@root.com"
            }
            notice = ab.build_notice(error, user=user)

            exception_str = type(e).__name__
            exception_type = type(e).__name__

            expected_payload = self.get_expected_payload(exception_str,
                                                         exception_type)

            data = {
                'type': exc_info[1].__class__.__name__,
                'backtrace': format_backtrace(exc_info[2]),
                'message': pytb_lastline(exc_info)
            }

            expected_payload['errors'] = [data]
            expected_payload['context']['user'] = user
            expected_payload['context']['severity'] = ErrorLevels.DEFAULT_LEVEL

            self.assertEqual(expected_payload, notice.payload)

            with mock.patch('requests.post') as requests_post:
                ab.notify(error)
                data = json.loads(requests_post.call_args[1]['data'])
                self.assertEqual(expected_payload, data)

    def test_deploy_payload(self):
        with mock.patch('requests.post') as requests_post:
            ab = Airbrake(project_id=1234, api_key='fake', environment='test')
            ab.deploy('test',
                      'user1',
                      'https://github.com/airbrake/airbrake',
                      '38748467ea579e7ae64f7815452307c9d05e05c5',
                      'v2.0')

            expected_call_args = mock.call(
                'https://api.airbrake.io/api/v4/projects/1234/deploys',
                data='{"environment": "test",'
                     ' "repository": "https://github.com/airbrake/airbrake",'
                     ' "revision": "38748467ea579e7ae64f7815452307c9d05e05c5",'
                     ' "username": "user1",'
                     ' "version": "v2.0"}',
                headers={'Content-Type': 'application/json'},
                params={'key': 'fake'},
                timeout=Airbrake.AIRBRAKE_TIMEOUT_DEFAULT
            )
            self.assertEqual(expected_call_args, requests_post.call_args)

    def test_deploy_revision(self):
        with mock.patch('requests.post') as requests_post:
            ab = Airbrake(project_id=1234, api_key='fake', environment='test')
            ab.deploy('test',
                      'user1',
                      'https://github.com/airbrake/airbrake',
                      None,
                      'v2.0')

            data = json.loads(requests_post.call_args[1]['data'])
            version = airbrake.utils.get_local_git_revision()

            self.assertEqual(version, data['revision'])

    def check_timeout(self, timeout=None, expected_timeout=None):
        ab = Airbrake(project_id=1234,
                      api_key='fake',
                      environment='test',
                      timeout=timeout)
        if not timeout:
            ab = Airbrake(project_id=1234,
                          api_key='fake',
                          environment='test')

        with mock.patch('requests.post') as requests_post:
            ab.deploy('test', 'user1')
            timeout = requests_post.call_args[1]['timeout']
            self.assertEqual(expected_timeout, timeout)

        with mock.patch('requests.post') as requests_post:
            notice = ab.build_notice("This is a test")
            ab.notify(notice)
            timeout = requests_post.call_args[1]['timeout']
            self.assertEqual(expected_timeout, timeout)

    def test_timeouts(self):
        self.check_timeout(expected_timeout=5)
        self.check_timeout(-1, -1)
        self.check_timeout(5, 5)

    def check_filter(self, ab, expected_params):
        params = {
            "filter_me_i_dare_you": "super secret msg",
            "blacklist_me": "I double dare you",
            "page": 1,
            "order": "desc"
        }

        notice = ab.build_notice("This is a test", params)

        with mock.patch('requests.post') as requests_post:
            ab.notify(notice)
            data = json.loads(requests_post.call_args[1]['data'])
            self.assertEqual(expected_params, data["params"])

    def test_whitelist(self):
        ab = Airbrake(project_id=1234,
                      api_key='fake',
                      whitelist_keys=["page", "order"])
        expected_params = {
            "filter_me_i_dare_you": "[Filtered]",
            "blacklist_me": "[Filtered]",
            "page": 1,
            "order": "desc"
        }

        self.check_filter(ab, expected_params)

    def test_blacklist(self):
        ab = Airbrake(project_id=1234,
                      api_key='fake',
                      blacklist_keys=["filter_me_i_dare_you", "blacklist_me"])
        expected_params = {
            "filter_me_i_dare_you": "[Filtered]",
            "blacklist_me": "[Filtered]",
            "page": 1,
            "order": "desc"
        }

        self.check_filter(ab, expected_params)

    def test_mixed_filter(self):
        ab = Airbrake(project_id=1234,
                      api_key='fake',
                      whitelist_keys=["page",
                                      "order",
                                      "filter_me_i_dare_you"],
                      blacklist_keys=["filter_me_i_dare_you"])
        expected_params = {
            "filter_me_i_dare_you": "[Filtered]",
            "blacklist_me": "[Filtered]",
            "page": 1,
            "order": "desc"
        }

        self.check_filter(ab, expected_params)

    def test_notice_severity(self):
        ab = Airbrake(project_id=1234, api_key='fake')
        notice = ab.build_notice(ValueError("This is a test"),
                                 severity=ErrorLevels.CRITICAL)

        self.assertEqual(ErrorLevels.CRITICAL,
                         notice.payload['context']['severity'])

        with mock.patch('requests.post') as requests_post:
            ab.notify(notice)
            data = json.loads(requests_post.call_args[1]['data'])
            error_level = data['context']['severity']
            self.assertEqual(ErrorLevels.CRITICAL, error_level)

    def test_log_critical(self):
        msg = "Sassafraz!"
        with mock.patch.object(Airbrake, 'notify') as notify:
            self.assertTrue(self.logger.isEnabledFor(logging.CRITICAL))
            self.logger.critical(msg)
            data = notify.call_args[0][0].payload
            self.assertEqual(ErrorLevels.CRITICAL,
                             data['context']['severity'])

    def test_uncaught_exception(self):
        ab = Airbrake(project_id=1234, api_key='fake')
        self.preserved_syshook = False

        def early_exit_syshook(*exc_info):
            self.preserved_syshook = True
            return

        ab.excepthook = early_exit_syshook

        with mock.patch('requests.post') as requests_post:
            try:
                raise Exception("raise to sys level")
            except Exception:
                # nose wraps exceptions, so manually call the exception as
                # if it was uncaught.
                exc_info = sys.exc_info()

                sys.excepthook(*exc_info)

            data = json.loads(requests_post.call_args[1]['data'])
            error_level = data['context']['severity']
            self.assertEqual(ErrorLevels.ERROR, error_level)
            self.assertTrue(self.preserved_syshook)


if __name__ == '__main__':
    unittest.main()
