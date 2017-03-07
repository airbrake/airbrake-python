import airbrake
import mock
import platform
import socket
import unittest
import json
import sys
import traceback

from airbrake.notifier import Airbrake
from airbrake.notice import Error, format_backtrace
from airbrake.utils import pytb_lastline
from airbrake.__about__ import __version__
from airbrake.__about__ import __url__


class TestAirbrakeNotifier(unittest.TestCase):

    def _create_notify(test, exception, session={},
                       environment={}, context={}, **params):
        def notify(self, payload):

            test.assertEqual(session, payload['session'])
            test.assertEqual(environment, payload['environment'])
            test.assertEqual(str(exception), payload['errors'][0]['message'])
            test.assertEqual(context, payload['context'])
            for param_name, expected_value in params.items():
                test.assertEqual(expected_value, payload['params'][param_name])
        return notify

    def setUp(self):
        super(TestAirbrakeNotifier, self).setUp()
        self.logger = airbrake.getLogger(
            'custom-loglevel',
            api_key='fakekey', project_id='fakeprojectid')
        self.session = {'user_id': 100}
        self.environment = {'PATH': '/usr/bin/'}
        self.context = {'environment': socket.gethostname(),
                        'hostname': socket.gethostname(),
                        'os': platform.platform(),
                        'language': 'Python %s' % platform.python_version()}

    def test_string(self):
        msg = "Zlonk!"
        notify = self._create_notify(msg)
        with mock.patch.object(Airbrake, 'notify', notify):
            self.logger.exception(msg)

    def test_exception(self):
        msg = "Pow!"
        notify = self._create_notify(Exception(msg))
        with mock.patch.object(Airbrake, 'notify', notify):
            self.logger.exception(Exception(msg))

    def test_exception_with_session(self):
        msg = "Boff!"
        notify = self._create_notify(msg, session=self.session)
        with mock.patch.object(Airbrake, 'notify', notify):
            extra = {'session': self.session}
            self.logger.exception(Exception(msg), extra=extra)

    def test_exception_with_environment(self):
        msg = "Whap!"
        notify = self._create_notify(msg, environment=self.environment)
        with mock.patch.object(Airbrake, 'notify', notify):
            extra = {'environment': self.environment}
            self.logger.exception(Exception(msg), extra=extra)

    def test_exception_with_context(self):
        msg = "Zonk!"
        notify = self._create_notify(msg, context=self.context)
        with mock.patch.object(Airbrake, 'notify', notify):
            self.logger.exception(Exception(msg))

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
            self.logger.exception(Exception(msg), extra=extra)

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
            }

            data = json.loads(requests_post.call_args[1]['data'])
            actual_context = data["context"]

            self.assertEqual(expected_context, actual_context)

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
                'version': '1.3.4',
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
            notice = ab.build_notice(error)

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
                'https://airbrake.io/api/v4/projects/1234/deploys',
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


if __name__ == '__main__':
    unittest.main()
