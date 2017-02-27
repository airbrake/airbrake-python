import airbrake
import mock
import platform
import socket
import unittest
import json

from airbrake.notifier import Airbrake
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

    def test_notify_payload(self):
        # 1d7b191a2cc3b53f76f12d09f68c857183859e08 broke the `notify interface
        # by making the assumption that the payload sent to `notify` is already
        # encoded as a JSON string.
        # This test ensures that such a regression can't happen again.
        with mock.patch('requests.post') as requests_post:
            ab = Airbrake(project_id=1234, api_key='fake', environment='test')
            payload = dict(foo=1, bar=2)
            ab.notify(payload)

            expected_call_args = mock.call(
                'https://airbrake.io/api/v3/projects/1234/notices',
                data='{"bar": 2, "foo": 1}',
                headers={'Content-Type': 'application/json'},
                params={'key': 'fake'}
            )
            self.assertEqual(expected_call_args, requests_post.call_args)

    def test_notify_context(self):
        with mock.patch('requests.post') as requests_post:
            version = platform.python_version()
            plat = platform.platform()
            hostname = u"test-host"
            environment = u"testing123"
            root_directory = u"/home/app/"
            ab = Airbrake(project_id=1234, api_key='fake', hostname=hostname,
                          environment=environment, app_version=app_version,
                          app_url=app_url, root_directory=root_directory,
                          user_id=user_id, user_name=user_name,
                          user_email=user_email)
            ab.log("this is a test")

            expected_context = {
                u'notifier': {
                    u'name': u'airbrake-python',
                    u'version': __version__,
                    u'url': __url__
                },
                u'os': plat,
                u'hostname': hostname,
                u'language': u'Python/%s' % version,
                u'environment': environment,
                u'rootDirectory': root_directory,
            }

            data = json.loads(requests_post.call_args[1]['data'])
            actual_context = data["context"]

            self.assertEqual(expected_context, actual_context)

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
                params={'key': 'fake'}
            )
            self.assertEqual(expected_call_args, requests_post.call_args)


if __name__ == '__main__':
    unittest.main()
