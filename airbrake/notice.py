"""Airbrake Notice module.

Wrapper classes for converting various types of data into Airbrake formatted
errors
"""

import traceback
from airbrake import utils


class Notice(object):  # pylint: disable=too-few-public-methods
    """Create Airbrake formatted notice objects from a variety of objects."""

    def __init__(self, exception, params=None, session=None,
                 environment=None, context=None, notifier=None):
        """Client Constructor."""

        self.exception = exception
        self.params = params
        self.session = session
        self.environment = environment
        self.context = context
        self.notifier = notifier

        if isinstance(exception, str):
            error = {
                'type': "Error",
                'backtrace': [{'file': "N/A",
                               'line': 1,
                               'function': "N/A"}],
                'message': exception}
            self.errors = [error]

        if isinstance(exception, Exception) or \
                isinstance(exception, BaseException):
            error = {
                'type': type(exception).__name__,
                'backtrace': [{'file': "N/A",
                               'line': 1,
                               'function': "N/A"}],
                'message': str(exception)}
            self.errors = [error]

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


class Error(object):  # pylint: disable=too-few-public-methods
    """Format the exception according to airbrake.io v3 API.

    The airbrake.io docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3
    """

    def __init__(self, exc_info=None, message=None, filename=None,
                 line=None, function=None, errtype=None):
        """Error object constructor."""
        self.exc_info = exc_info

        # default datastructure
        self.data = {
            'type': errtype or "Record",
            'backtrace': [{'file': filename or "N/A",
                           'line': line or 1,
                           'function': function or "N/A"}],
            'message': message or "N/A"}

        if utils.is_exc_info_tuple(self.exc_info):
            if not all(self.exc_info):
                return
            tbmessage = utils.pytb_lastline(self.exc_info)
            self.data.update(
                {'type': self.exc_info[1].__class__.__name__,
                 'backtrace': format_backtrace(self.exc_info[2]),
                 'message': message or tbmessage})
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
