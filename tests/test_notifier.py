import airbrake
import mock
import unittest
import json

from airbrake.notifier import Airbrake


class TestAirbrakeNotifier(unittest.TestCase):

    def _create_notify(test, exception, session={}, environment={}, **params):
        def notify(self, payload):
            payload = json.loads(payload)
            test.assertEqual(session, payload['session'])
            test.assertEqual(environment, payload['environment'])
            test.assertEqual(str(exception), payload['errors'][0]['message'])
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

if __name__ == '__main__':
    unittest.main()
