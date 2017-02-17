import airbrake
import mock
import platform
import socket
import unittest

from airbrake.notifier import Airbrake


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


if __name__ == '__main__':
    unittest.main()
