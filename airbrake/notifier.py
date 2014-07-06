"""Airbrake object to handle airbrake.io reporting."""
import json
import os
import platform
import socket
import sys
import traceback
import urlparse
import warnings

import requests

from airbrake import _notifier as airbrake_python_notifier
from airbrake import utils


class Airbrake(object):
    """
    Class to handle exceptions that need to be sent to airbrake.io

    The payload (dict) to be POSTed as json is defined by an
    instance's `payload` attribute, which can be modified after
    Airbrake instantiation.

    If auto_notify=True (default), errors logged ( using Airbrake.log() )
    will automatically be shipped; otherwise, logged errors will be
    aggregated and shipped as a group when Airbrake.notify() is called.

    Non-logging Handler usage:

    // Auto-notify is enabled by default

        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234")

        try:
            1/0
        except Exception:
            ab.log()

    If auto-notify is disabled:

        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234", auto_notify=False)

        try:
            1/0
        except Exception as exc:
            ab.log()

        # more code, possible errors

        ab.notify()

    The airbrake.io docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3
    """

    def __init__(self, project_id=None, api_key=None, environment=None,
                 use_ssl=True, auto_notify=True):

        #properties
        self._api_url = None
        self._env_context = None
        self.deploy_url = "http://api.airbrake.io/deploys.txt"
        self.notifier = airbrake_python_notifier

        if not environment:
            environment = (os.getenv('AIRBRAKE_ENVIRONMENT') or
                           socket.gethostname())
        if not project_id:
            project_id = os.getenv('AIRBRAKE_PROJECT_ID', '')
        if not api_key:
            api_key = os.getenv('AIRBRAKE_API_KEY', '')

        self.environment = str(environment)
        self.project_id = str(project_id)
        self.api_key = str(api_key)
        self.auto_notify = auto_notify
        self.use_ssl = use_ssl
        self.errors = []
        self.payload_params = {}
        self.payload_session = {}
        self.payload = {'context': self.context,
                        'params': self.payload_params,
                        'errors': self.errors,
                        'notifier': self.notifier,
                        'environment': {},
                        'session': self.payload_session}

        if not all((self.project_id, self.api_key)):
            raise TypeError("Airbrake API Key (api_key) and Project ID "
                            "(project_id) must be set. These values "
                            "may be set using the environment variables "
                            "AIRBRAKE_API_KEY and AIRBRAKE_PROJECT_ID or "
                            "by passing in the arguments explicitly.")

    def __repr__(self):
        return ("Airbrake(project_id=%s, api_key=*****, environment=%s, "
                "use_ssl=%s, auto_notify=%s"
                % (self.project_id, self.environment,
                   self.use_ssl, self.auto_notify))

    @property
    def context(self):
        """Contains the python, os, and app environment context."""
        if not self._env_context:
            self._env_context = {}
            # python
            version = platform.python_version()
            self._env_context.update({'language': 'Python %s' % version})
            # os
            plat = platform.platform()
            self._env_context.update({'os': plat})
            # env name
            self._env_context.update({'environment': self.environment})
            # TODO(samstav)
            #   add user info:
            #       userID, userName, userEmail
            #   add application info:
            #       version, url, rootDirectory
        return self._env_context

    @property
    def api_url(self):
        """Create the airbrake api endpoint and return a string."""
        if not self._api_url:
            self._api_url = (
                 "https://airbrake.io/api/v3/projects/%s/notices"
                  % self.project_id)
        return self._api_url

    def log(self, exc_info=None, message=None, filename=None,
            line=None, function=None, errtype=None, **params):
        """Acknowledge an error, prepare it to be shipped to Airbrake,
        and append to Airbrake.errors. If Airbrake.auto_notify=True, the error
        will also be shipped to Airbrake immediately; otherwise, all
        logged errors will be shipped on the next call to Airbrake.notify().

        :param exc_info:    Exception tuple to use for formatting request.
        :param message:     Message accompanying error.
        :param filename:    Name of file where error occurred.
        :param line:        Line number in file where error occurred.
        :param function:    Function name where error occurred.
        :param errtype:     Type of error which occurred.
        :param params:      Payload field "params" which may contain any other
                            context related to the exception(s).
        """
        self.payload_params.update(params)

        if isinstance(exc_info, Exception):
            errmessage = utils.pytb_lastline(exc_info)
            exc_info = None
            if message:
                message = "%s | %s" % (message, errmessage)
            else:
                message = errmessage

        error = Error(
            exc_info=exc_info, message=message, filename=filename,
            line=line, function=function, errtype=errtype)
        self.errors.append(error.data)

        if self.auto_notify:
            self.notify()
        return error

    def notify(self):
        """Post the JSON body to airbrake.io. Ships all errors aggregated by
        Airbrake.log() and resets the errors list in `errors` attribute.
        """

        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}

        if not self.errors:
            return

        response = requests.post(self.api_url, data=json.dumps(self.payload),
                                 headers=headers, params=api_key)
        response.raise_for_status()
        self._reset()
        return response

    def _reset(self):
        del self.errors[:]
        self.payload_params.clear()
        self.payload_session.clear()

    def deploy(self, env=None):

        environment = env or self.environment

        params = {'api_key': self.api_key,
                  'deploy[rails_env]': str(environment)}

        response = requests.post(self.deploy_url, params=params)
        response.raise_for_status()
        return response.status_code


class Error(object):
    """Format the exception according to what is expected by airbrake.io.

    The airbrake.io docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3

    If the global sys.exc_info is to be read/used, it should be done here.
    """

    def __init__(self, exc_info=None, message=None, filename=None,
                 line=None, function=None, errtype=None):

        #default (to be overwritten)
        self.data = {
            'type': errtype or "Record",
            'backtrace': [{'file': filename or "N/A",
                           'line': line or 1,
                           'function': function or "N/A"}],
            'message': message or "N/A"}

        # get current exception info
        self._exc_info = sys.exc_info()
        if not exc_info:
            exc_info = self._exc_info
        self.exc_info = exc_info

        if len(self.exc_info) == 3 and isinstance(self.exc_info, tuple):
            if not all(self.exc_info):
                return
            # if exc_info is a FQ exception info tuple
            try:
                # using method from traceback module to verify the tuple
                self.formatted_exc = traceback.format_exception(*self.exc_info)
            except (AttributeError, TypeError) as err:
                err.message = ("Airbrake module received unsupported "
                                "'exc_info' type. Should be a sys.exc_info() "
                                "tuple, a string, or None. Invalid argument "
                                "was %s | %s"
                                % (self.exc_info, err.message))
                raise err.__class__(err.message)

            tbmessage = utils.pytb_lastline(self.exc_info)
            self.data.update(
                {'type': self.exc_info[1].__class__.__name__,
                'backtrace': self.format_backtrace(self.exc_info[2]),
                'message': tbmessage})
        else:
            raise ValueError("Airbrake module received unsupported "
                                "'exc_info' type. Should be a sys.exc_info() "
                                "tuple. Invalid argument was of type %s"
                                % type(self.exc_info))

    def format_backtrace(self, trace):
        """Format backtrace dict and append to the array of errors
        managed by the Airbrake instance."""
        backtrace = []
        for filename, line, func, _ in traceback.extract_tb(trace):
            desc = {'file': filename,
                    'line': line,
                    'function': func}
            backtrace.append(desc)
        return backtrace
