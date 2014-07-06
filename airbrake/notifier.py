"""Airbrake notifier client module.

Initialize this class to ship errors to airbrake.io
using the log() method.
"""
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
    Class to handle exceptions, format & ship to airbrake.io.

    The payload (dict) to be POSTed as json is defined by an
    instance's `payload` attribute, which can be modified after
    Airbrake instantiation.

    Errors logged ( using Airbrake.log() ) will automatically be shipped.

    Usage *without* AirbrakeHandler:

        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234")

        try:
            1/0
        except Exception:
            ab.log()

    The airbrake.io docs used to implement this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3
    """

    def __init__(self, project_id=None, api_key=None, environment=None):

        #properties
        self._api_url = None
        self._context = None
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
        return ("Airbrake(project_id=%s, api_key=*****, environment=%s)"
                % (self.project_id, self.environment))

    @property
    def context(self):
        """Contains the python, os, and app environment context."""
        if not self._context:
            self._context = {}
            # python
            version = platform.python_version()
            self._context.update({'language': 'Python %s' % version})
            # os
            plat = platform.platform()
            self._context.update({'os': plat})
            # env name
            self._context.update({'environment': self.environment})
            # TODO(samstav)
            #   add user info:
            #       userID, userName, userEmail
            #   add application info:
            #       version, url, rootDirectory
        return self._context

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
        """Acknowledge an error and post it to airbrake.io.

        :param exc_info:    Exception tuple to use for formatting request.
        :param message:     Message accompanying error.
        :param filename:    Name of file where error occurred.
        :param line:        Line number in file where error occurred.
        :param function:    Function name where error occurred.
        :param errtype:     Type of error which occurred.
        :param params:      Payload field "params" which may contain any other
                            context related to the exception(s).
        """

        if not utils.is_exc_info_tuple(exc_info):
            # compatibility, allows exc_info not to be a exc tuple
            errmessage = None
            if isinstance(exc_info, Exception):
                errmessage = utils.pytb_lastline(exc_info)
            elif exc_info:
                try:
                    errmessage = json.dumps(exc_info)
                except (ValueError, TypeError):
                    errmessage = str(exc_info)
            if errmessage:
                # this way, if exc_info kwarg is passed to logger method,
                # its value will be available in params
                params['exc_info'] = errmessage

            if message and errmessage and message != errmessage:
                message = "%s | %s" % (message, errmessage)
            elif errmessage:
                message = errmessage

            exc_info = sys.exc_info()

        self.payload_params.update(params)

        error = Error(
            exc_info=exc_info, message=message, filename=filename,
            line=line, function=function, errtype=errtype)
        self.errors.append(error.data)

        return self.notify()

    def notify(self):
        """Post the current errors payload body to airbrake.io.

        Resets the errors list in self.errors
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

        self.exc_info = exc_info

        #default datastructure
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
                 'message': tbmessage})
        else:
            raise TypeError(
                "Airbrake module (notifier.Error) received "
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
