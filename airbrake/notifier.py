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

import requests

from airbrake.__about__ import __notifier__
from airbrake import exc as ab_exc
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

    def __init__(self, project_id=None, api_key=None, environment=None,
                 base_url=None):
        """Client constructor."""
        # properties
        self._api_url = None
        self._context = None
        self.deploy_url = "http://api.airbrake.io/deploys.txt"
        self.notifier = __notifier__

        if not environment:
            environment = (os.getenv('AIRBRAKE_ENVIRONMENT') or
                           socket.gethostname())
        if not project_id:
            project_id = os.getenv('AIRBRAKE_PROJECT_ID', '')
        if not api_key:
            api_key = os.getenv('AIRBRAKE_API_KEY', '')
        if not base_url:
            base_url = os.getenv('AIRBRAKE_BASE_URL',
                                 'https://airbrake.io').strip('/')

        self.environment = str(environment)
        self.project_id = str(project_id)
        self.api_key = str(api_key)
        self.base_url = str(base_url)

        if not all((self.project_id, self.api_key)):
            raise ab_exc.AirbrakeNotConfigured(
                "Airbrake API Key (api_key) and Project ID "
                "(project_id) must be set. These values "
                "may be set using the environment variables "
                "AIRBRAKE_API_KEY and AIRBRAKE_PROJECT_ID or "
                "by passing in the arguments explicitly."
            )

        self._exc_queue = utils.CheckableQueue()

    def __repr__(self):
        """Return value for the repr function."""
        return ("Airbrake(project_id=%s, api_key=*****, environment=%s)"
                % (self.project_id, self.environment))

    @property
    def context(self):
        """The python, os, and app environment context."""
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
            self._api_url = "%s/api/v3/projects/%s/notices" % (
                self.base_url, self.project_id)
        return self._api_url

    def log(self, exc_info=None, message=None, filename=None,
            line=None, function=None, errtype=None, **params):
        """Acknowledge an error and post it to airbrake.io.

        :param exc_info:    Exception tuple to use for formatting request.
                            If None, sys.exc_info() will be read to get
                            exception info. To prevent the reading of
                            sys.exc_info(), set exc_info to False.
        :param message:     Message accompanying error.
        :param filename:    Name of file where error occurred.
        :param line:        Line number in file where error occurred.
        :param function:    Function name where error occurred.
        :param errtype:     Type of error which occurred.
        :param params:      Payload field "params" which may contain any other
                            context related to the exception(s).

        Exception info willl be read from sys.exc_info() if it is not
        supplied. To prevent this behavior, pass exc_info=False.
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

            # read the global exception stack, but
            # be sure not to read the same exception twice.
            # This can happen for a number of reasons:
            #   - the exception context has not been
            #     cleared or garbage collected
            #   - the airbrake logging handler is being used
            #     to log exceptions and error messages in the same
            #     thread, but that thread is not actually logging
            #     some exceptions, or is not clearing the exception
            #     context via sys.exc_clear()
            # the alternative is to clear the exception stack every time,
            # which this module *should not* take the liberty to do
            #
            # to prevent this function from reading the global
            # exception context *at all*, pass exc_info=False
            if exc_info is False:
                exc_info = None, None, None
            else:
                exc_info = sys.exc_info()

        # dont ship the same exception instance twice
        if exc_info[1] in self._exc_queue:
            exc_info = None, None, None
        self._exc_queue.put(exc_info[1])

        error = Error(
            exc_info=exc_info, message=message, filename=filename,
            line=line, function=function, errtype=errtype)
        environment = params.pop('environment', {})
        session = params.pop('session', {})
        payload = {'context': self.context,
                   'params': params,
                   'errors': [error.data],
                   'notifier': self.notifier,
                   'environment': environment,
                   'session': session}
        return self.notify(payload)

    def notify(self, payload):
        """Post the current errors payload body to airbrake.io.

        :param dict payload:
            Notification payload, in a dict/object form. The notification
            payload will ultimately be sent as a JSON-encoded string, but here
            it still needs to be in object form.
        """
        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}
        response = requests.post(
            self.api_url,
            data=json.dumps(payload, cls=utils.FailProofJSONEncoder,
                            sort_keys=True),
            headers=headers,
            params=api_key)
        response.raise_for_status()
        return response

    def deploy(self, env=None):
        """Reset counted errors for the airbrake project/environment."""
        environment = env or self.environment

        params = {'api_key': self.api_key,
                  'deploy[rails_env]': str(environment)}

        response = requests.post(self.deploy_url, params=params)
        response.raise_for_status()
        return response


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
