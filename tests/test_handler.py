import logging
import unittest

from testfixtures import log_capture

import airbrake



class TestAirbrakeLoggerHelper(unittest.TestCase):

    def test_auto_logger_name_is_calling_module(self):
        logger = airbrake.getLogger()
        self.assertEqual(logger.name, airbrake.DEFAULT_LOGGER_PREFIX + __name__)

    def test_auto_logger_has_airbrake_handler(self):
        logger = airbrake.getLogger()
        isabhandler = lambda x: isinstance(x, airbrake.AirbrakeHandler)
        self.assertTrue(any(map(isabhandler, logger.handlers)))

    def test_auto_logger_has_level(self):
        logger = airbrake.getLogger()
        self.assertTrue(
            logger.isEnabledFor(airbrake.handler.DEFAULT_LOGGING_LEVEL))

    def test_auto_logger_given_name(self):
        logger = airbrake.getLogger('my_module')
        self.assertTrue(
            logger.isEnabledFor(airbrake.handler.DEFAULT_LOGGING_LEVEL))

class TestAirbrakeHandler(unittest.TestCase):

    def setUp(self):
        self.logger = airbrake.getLogger()
        self.logmsg = "There's your problem, right there."

    @log_capture(level=airbrake.handler.DEFAULT_LOGGING_LEVEL)
    def do_some_logs(self, l):
        self.logger.info("Should ignore this by default.")
        self.logger.error(self.logmsg)
        return l

    def log_in_exception_handler(self):
        try:
            1/0
        except Exception:
            self.logger.exception("Hate when this happens.", extra={'this': 'wins'})

        try:
            undefined
        except Exception:
            self.logger.error("It's bad luck not to assign values.")

    def test_log_captures(self):
        captured = self.do_some_logs()
        captured.check(
            (airbrake.DEFAULT_LOGGER_PREFIX + __name__,
             logging._levelNames[airbrake.handler.DEFAULT_LOGGING_LEVEL],
             self.logmsg))

    def test_exception(self):
        self.log_in_exception_handler()

if __name__ == '__main__':
    unittest.main()
