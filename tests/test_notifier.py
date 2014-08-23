import airbrake
import mock
import unittest
from airbrake.notifier import Airbrake


class TestAirbrakeNotifier(unittest.TestCase):

    def _create_notify(test, exception, session={}, environment={}):
        def notify(self, payload):
            test.assertEqual(session, payload['session'])
            test.assertEqual(environment, payload['environment'])
            test.assertEqual(str(exception), payload['errors'][0]['message'])
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

if __name__ == '__main__':
    unittest.main()
