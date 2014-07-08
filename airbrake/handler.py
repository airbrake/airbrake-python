"""AirbrakeHandler module.

All functions and types related to python logging
should be defined in this module.

A function for mapping a LogRecord object
    https://docs.python.org/2/library/logging.html#logrecord-objects
to an Airbrake error should be included here.
"""
import logging
import sys

from airbrake import Airbrake

_fake_logrecord = logging.LogRecord('', '', '', '', '', '', '', '')


class AirbrakeHandler(logging.Handler):

    """
    A handler class which ships logs to airbrake.io

    Requires one:
        * `project_id` AND `api_key`
        * an instance of airbrake.Airbrake
    """

    def __init__(self, airbrake=None, level=logging.ERROR, **kwargs):
        """Initialize the Airbrake handler with a default logging level.

        Default level of logs handled by this class are >= ERROR,
        which includes ERROR and CRITICAL. To change this behavior
        supply a different arguement for 'level'.

        All 'kwargs' will be passed to notifier.Airbrake to instantiate
        a notifier client.
        """

        logging.Handler.__init__(self, level=level)

        if isinstance(airbrake, Airbrake):
            self.airbrake = airbrake
        else:
            self.airbrake = Airbrake(**kwargs)

    def emit(self, record):
        try:
            airbrakeerror = airbrake_error_from_logrecord(record)
            self.airbrake.log(**airbrakeerror)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def airbrake_error_from_logrecord(record):
    """Create an airbrake error dictionary from a python LogRecord object.

    For more info on the logging.LogRecord class:
        https://docs.python.org/2/library/logging.html#logrecord-objects
    """
    airbrakeerror = {}
    params = {
        'created': record.created,  # TODO(samstav): make this human readable
        'process_id': record.process,
        'process_name': record.processName,
        'thread_name': record.threadName,
        'lineno': record.lineno,
        'pathname': record.pathname,
        'funcName': record.funcName,
        'msg': record.getMessage()}

    # find params from kwarg 'extra'
    for key, val in vars(record).items():
        if not hasattr(_fake_logrecord, key):
            params[key] = val

    if sys.exc_info()[1]:
        airbrakeerror['errtype'] = sys.exc_info()[1].__class__.__name__
    else:
        # set the errtype even if there's no current exception stackframe
        airbrakeerror['errtype'] = "%s:%s" % (record.levelname,
                                              record.filename)

    airbrakeerror.update(params)
    airbrakeerror['exc_info'] = record.exc_info
    airbrakeerror['message'] = record.getMessage()
    airbrakeerror['filename'] = record.pathname
    airbrakeerror['line'] = record.lineno
    airbrakeerror['function'] = record.funcName
    return airbrakeerror
