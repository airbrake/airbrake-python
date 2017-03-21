"""AirbrakeHandler module.

All functions and types related to python logging
should be defined in this module.

A function for mapping a LogRecord object
    https://docs.python.org/2/library/logging.html#logrecord-objects
to an Airbrake error should be included here.
"""
import logging

from airbrake.notifier import Airbrake
from airbrake.notice import ErrorLevels

_FAKE_LOGRECORD = logging.LogRecord('', '', '', '', '', '', '', '')


class AirbrakeHandler(logging.Handler):
    """A handler class which ships logs to airbrake.io.

    Requires one:
        * `project_id` AND `api_key`
        * an instance of airbrake.Airbrake
    """

    # pylint: disable=too-many-arguments

    def __init__(self, airbrake=None, level=logging.ERROR, project_id=None,
                 api_key=None, **config):
        """Initialize the Airbrake handler with a default logging level.

        Default level of logs handled by this class are >= ERROR,
        which includes ERROR and CRITICAL. To change this behavior
        supply a different argument for 'level'.
        """

        logging.Handler.__init__(self, level=level)

        if isinstance(airbrake, Airbrake):
            self.airbrake = airbrake
        else:
            self.airbrake = Airbrake(project_id, api_key, **config)

    def emit(self, record):
        """Log the record airbrake.io style.

        To prevent method calls which invoke this handler from using the
        global exception context in sys.exc_info(), exc_info must be passed
        as False.

        E.g. To prevent AirbrakeHandler from reading the global exception
        context, (which it may do to find a traceback and error type), make
        logger method calls like this:

            LOG.error("Bad math.", exc_info=False)

        Otherwise, provide exception context directly, though the following
        contrived example would be a strange way to use the handler:

            exc_info = sys.exc_info()
            ...
            LOG.error("Bad math.", exc_info=exc_info)
        """
        # if record.exc_info[1]:
        #     print("record.exc_info[1], ", record.exc_info[1])
        #     record.exc_info[1].__context__
        #     print("wtf?, ", record.exc_info[1].__context__)

        try:
            airbrakeerror = airbrake_error_from_logrecord(record)
            self.airbrake.log(**airbrakeerror)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # pylint: disable=bare-except
            self.handleError(record)


def airbrake_error_from_logrecord(record):
    """Create an airbrake error dictionary from a python LogRecord object.

    For more info on the logging.LogRecord class:
        https://docs.python.org/2/library/logging.html#logrecord-objects
    """
    airbrakeerror = {}
    params = {
        'logrecord_filename': record.filename,
        'levelname': record.levelname,
        'created': record.created,  # TODO(samstav): make this human readable
        'process_id': record.process,
        'process_name': record.processName,
        'thread_name': record.threadName,
        'lineno': record.lineno,
        'pathname': record.pathname,
        'funcName': record.funcName,
        'msg': record.getMessage()}

    # find params from kwarg 'extra'
    # See "The second keyword argument is extra"
    #   - https://docs.python.org/2/library/logging.html#logging.Logger.debug
    for key, val in list(vars(record).items()):
        if not hasattr(_FAKE_LOGRECORD, key):
            # handle attribute/field name collisions:
            # logrecod attrs should not limit or take
            # precedence over values specified in 'extra'
            if key in params:
                # if key "already" in params -> is logrecord attr
                params["logrecord_" + key] = params.pop(key)
            # let 'extra' (explicit) take precedence
            params[key] = val

    airbrakeerror.update(params)
    # errtype may be overridden by the notifier if an applicable
    # exception context is available and exc_info is not False

    airbrakeerror['errtype'] = "%s:%s" % (record.levelname, record.filename)
    # if record.exc_info:
    #     getattr(record.exc_info[1], '__context__', None)
    #     # typ, err, tb = record.exc_info
    #     # getattr(err, '__context__', None)

    airbrakeerror['exc_info'] = record.exc_info
    airbrakeerror['message'] = record.getMessage()
    airbrakeerror['filename'] = record.pathname
    airbrakeerror['line'] = record.lineno
    airbrakeerror['function'] = record.funcName
    airbrakeerror['severity'] = getattr(ErrorLevels, record.levelname)
    return airbrakeerror
