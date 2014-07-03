import logging
import sys

from airbrake import Airbrake

DEFAULT_LOGGING_LEVEL = logging.ERROR
FAKE_LOGRECORD = logging.LogRecord(*8*('',))

class AirbrakeHandler(logging.Handler):
    """
    A handler class which ships logs to airbrake.io

    Requires one:
        * `project_id` AND `api_key`
        * an instance of airbrake.Airbrake
    """
    def __init__(self, airbrake=None, level=DEFAULT_LOGGING_LEVEL, **kwargs):
        """Initialize the Airbrake handler with a default loggin level.

        Default level of logs handled by this class are >= ERROR,
        which includes ERROR and CRITICAL. To change this behavior
        supply a different arguement for 'level'.
        """

        logging.Handler.__init__(self, level=level)

        if isinstance(airbrake, Airbrake):
            airbrake.auto_notify = True
            self.airbrake = airbrake
        else:
            kwargs.pop('auto_notify', '')
            self.airbrake = Airbrake(auto_notify=True, **kwargs)

    def emit(self, record):
        try:
            params = {
                'created': record.created,
                'process_id': record.process,
                'process_name': record.processName,
                'thread_name': record.threadName,
                'lineno': record.lineno,
                'pathname': record.pathname,
                'funcName': record.funcName,
                'msg': record.getMessage()}

            # find params from kwarg 'extra'
            for key, val in vars(record).items():
                if not hasattr(FAKE_LOGRECORD, key):
                    params[key] = val

            errtype = "%s:%s" % (record.levelname, record.filename)
            self.airbrake.log(
                exc_info=record.exc_info, message=record.getMessage(),
                filename=record.pathname, line=record.lineno,
                function=record.funcName, errtype=errtype, **params)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
