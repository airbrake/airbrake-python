import logging
import os
import unittest

import mock
from testfixtures import log_capture

import airbrake

BRAKE_LEVEL = 90
logging.addLevelName(BRAKE_LEVEL, "BRAKE")

def brake(self, message, *args, **kwargs):
    if self.isEnabledFor(BRAKE_LEVEL):
        self._log(BRAKE_LEVEL, message, args, **kwargs)
logging.Logger.brake = brake

class TestAirbrake(unittest.TestCase):

    def setUp(self):
        super(TestAirbrake, self).setUp()
        self.notify_patcher = mock.patch.object(
            airbrake.notifier.Airbrake, 'notify')
        self.notify_patcher.start()

    def tearDown(self):
        self.notify_patcher.stop()
        super(TestAirbrake, self).tearDown()


class TestAirbrakeHandlerBasic(TestAirbrake):

    def setUp(self):
        super(TestAirbrakeHandlerBasic, self).setUp()
        self.logger = airbrake.getLogger(
            api_key='fakekey', project_id='fakeprojectid')
        self.logmsg = "There's your problem, right there."

    def test_throws_missing_values(self):
        os.environ['AIRBRAKE_PROJECT_ID'] = ''
        os.environ['AIRBRAKE_API_KEY'] = ''
        self.assertRaises(TypeError, airbrake.getLogger)
        self.assertRaises(
            TypeError, airbrake.getLogger, project_id='fakeprojectid')
        self.assertRaises(
            TypeError, airbrake.getLogger, api_key='fakeapikey')


class TestCustomLogLevel(TestAirbrake):

    def setUp(self):
        super(TestCustomLogLevel, self).setUp()
        self.logger = airbrake.getLogger(
            'custom-loglevel',
            api_key='fakekey', project_id='fakeprojectid',
            level=BRAKE_LEVEL)

    def test_is_custom_level(self):
        self.abhandler = self.logger.handlers[0]
        self.assertTrue(self.abhandler.level == BRAKE_LEVEL,
            "%s is not %s" % (self.abhandler.level, BRAKE_LEVEL))

    def test_emit_call_count(self):
        self.abhandler = self.logger.handlers[0]
        self.abhandler.emit = mock.MagicMock()
        self.do_some_logs()
        self.assertTrue(self.abhandler.emit.call_count == 1)

    @log_capture(level=logging.INFO)
    def do_some_logs(self, l):
        levels = [lvl for lvl in logging._levelNames.keys()
                  if str(lvl).isdigit()]
        for level in levels:
            self.logger.log(level, "Hello.")
        return l

class TestAirbrakeLoggerHelper(TestAirbrakeHandlerBasic):

    def test_auto_logger_name_is_calling_module(self):
        self.assertEqual(
            self.logger.name, 'airbrake-python-' + __name__)

    def test_auto_logger_has_airbrake_handler(self):
        isabhandler = lambda x: isinstance(x, airbrake.AirbrakeHandler)
        self.assertTrue(any(map(isabhandler, self.logger.handlers)))

    def test_auto_logger_has_level(self):
        self.assertTrue(
            self.logger.isEnabledFor(logging.ERROR))

    def test_auto_logger_given_name(self):
        logger = airbrake.getLogger(
            'my_module', api_key='fakekey', project_id='fakeprojectid')
        self.assertTrue(
            logger.isEnabledFor(logging.ERROR))


class TestAirbrakeHandler(TestAirbrakeHandlerBasic):

    @log_capture(level=logging.ERROR)
    def do_some_logs(self, l):
        self.logger.info("Should ignore this by default.")
        self.logger.error(self.logmsg)
        return l

    def log_in_exception_handler(self):
        try:
            1/0
        except Exception:
            self.logger.exception("Hate when this happens.",
                                  extra={'this': 'wins'})

        try:
            undefined
        except Exception:
            self.logger.error("It's bad luck not to assign values.")

    def test_log_captures(self):
        captured = self.do_some_logs()
        captured.check(
            ('airbrake-python-' + __name__,
             logging._levelNames[logging.ERROR],
             self.logmsg))

    def test_exception(self):
        self.log_in_exception_handler()

if __name__ == '__main__':
    unittest.main()
