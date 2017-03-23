"""Airbrake Notice module.

Wrapper classes for converting various types of data into Airbrake formatted
errors
"""

import traceback
import sys
from airbrake import utils


class ErrorLevels(object):  # pylint: disable=too-few-public-methods,no-init
    """Convenience error levels."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERG = "emergency"

    DEFAULT_LEVEL = ERROR


class Notice(object):  # pylint: disable=too-few-public-methods
    """Create Airbrake formatted notice objects from a variety of objects."""

    # pylint: disable=too-many-arguments

    def __init__(self, exception, params=None, session=None,
                 environment=None, user=None, context=None,
                 notifier=None, severity=None):
        """Client Constructor."""

        self.exception = exception
        self.params = params
        self.session = session
        self.environment = environment
        self.context = context

        if user:
            data = _trim_data(user, ['id', 'name', 'email'])
            if not context:
                self.context = {}
            self.context["user"] = data

        self.notifier = notifier

        if isinstance(exception, str):
            error = {
                'type': "Error",
                'backtrace': [{'file': "N/A",
                               'line': 1,
                               'function': "N/A"}],
                'message': exception,
                'severity': severity or ErrorLevels.DEFAULT_LEVEL}
            self.errors = [error]

        if isinstance(exception, Exception) or \
                isinstance(exception, BaseException):
            error = {
                'type': type(exception).__name__,
                'backtrace': [{'file': "N/A",
                               'line': 1,
                               'function': "N/A"}],
                'message': str(exception),
                'severity': severity or ErrorLevels.DEFAULT_LEVEL}
            self.errors = [error]

        # Attempt to pull out error stacktrace if it's available.
        exc_info = sys.exc_info()
        if exc_info and exc_info[0]:
            err = Error(exc_info)
            self.errors = [err.data]

        if isinstance(exception, Error):
            self.errors = [exception.data]

    @property
    def payload(self):
        """Create a dict of all non-empty data in this notice."""
        return utils.non_empty_keys({'context': self.context,
                                     'params': self.params,
                                     'errors': self.errors,
                                     'notifier': self.notifier,
                                     'environment': self.environment,
                                     'session': self.session})


def _trim_data(ref_data, fields):
    """Trim only fields in dict and return errors."""
    data = {}
    for key in fields:
        data[key] = ref_data[key]
    return data


class Error(object):  # pylint: disable=too-few-public-methods
    """Format the exception according to airbrake.io v3 API.

    The airbrake.io docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3
    """

    # pylint: disable=too-many-arguments

    def __init__(self, exc_info=None, message=None, filename=None,
                 line=None, function=None, errtype=None,
                 severity=None):
        """Error object constructor."""
        self.exc_info = exc_info

        # default datastructure
        self.data = {
            'type': errtype or "Record",
            'backtrace': [{'file': filename or "N/A",
                           'line': line or 1,
                           'function': function or "N/A"}],
            'message': message or "N/A",
            'severity': severity or ErrorLevels.DEFAULT_LEVEL}

        if utils.is_exc_info_tuple(self.exc_info):
            if not all(self.exc_info):
                return
            tbmessage = utils.pytb_lastline(self.exc_info)
            self.data.update(
                {'type': self.exc_info[1].__class__.__name__,
                 'backtrace': format_backtrace(self.exc_info[2]),
                 'message': message or tbmessage,
                 'severity': severity or ErrorLevels.DEFAULT_LEVEL})
        else:
            raise TypeError(
                "Airbrake module (notice.Error) received "
                "unsupported 'exc_info' type. Should be a "
                "3-piece tuple as returned by sys.exc_info(). "
                "Invalid argument was %s"
                % self.exc_info)


def format_backtrace(trace):
    """Create a formatted dictionary from a traceback object."""
    backtrace = []
    for filename, line, func, _ in traceback.extract_tb(trace):
        desc = {'file': filename,
                'line': line,
                'function': func}
        backtrace.append(desc)
    return backtrace
