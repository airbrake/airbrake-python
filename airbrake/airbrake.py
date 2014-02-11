"""Airbrake object to handle airbrake.io reporting."""
import inspect
import json
import logging
import platform
import sys
import traceback
import urlparse

import requests

LOG = logging.getLogger(__name__)


class Airbrake(object):
    """
    Class to handle exceptions that need to be sent to airbrake.io

    The payload (dict) to be POSTed as json is defined by an
    instance's `payload` attribute, which can be modified after
    Airbrake instantiation.

    If auto_notify=True (default), errors logged ( using Airbrake.log() )
    will automatically be shipped; otherwise, logged errors will be
    aggregated and shipped as a group when Airbrake.notify() is called.

    Usage:

    Auto-notify is enabled by default:

        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234")

        try:
            1/0
        except Exception as exc:
            ab.log(exc)

    If auto-notify is disabled:

        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234", auto_notify=False)

        try:
            1/0
        except Exception as exc:
            ab.log(exc)

        # more code, possible errors

        ab.notify()

    The above are decent enough examples, but you'll probably want
    to include a `notifier` dictionary upon instantiating Airbrake.

    :param notifier: The notifier client. Describes the notifier
                     client submitting the request.
                     Should contain 'name', 'version', and 'url'
    :type notifier: dict

    The airbrake.io docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3
    """

    def __init__(self, project_id=None, api_key=None, environment="dev",
                 notifier=None, use_ssl=True, auto_notify=True):

        #properties
        self._api_url = None
        self._env_context = None
        self._calling_module = None
        self.deploy_url = "http://api.airbrake.io/deploys.txt"

        if notifier is None:
            notifier = {'name': self.calling_module,
                        'version': '1.0.0',
                        'url': 'http://app.example.com'}
        self.notifier = notifier

        self.auto_notify = auto_notify
        self.project_id = str(project_id)
        self.api_key = api_key
        self.use_ssl = use_ssl
        self.environment = str(environment)
        self.errors = []
        self.payload = {'context': self.context,
                        'params': {},
                        'errors': self.errors,
                        'notifier': self.notifier,
                        'environment': {},
                        'session': {}}

    def __repr__(self):
        return ("Airbrake(project_id=%s, api_key=*****, environment=%s, "
                "notifier=%s, use_ssl=%s, auto_notify=%s"
                % (self.project_id, self.environment, self.notifier,
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
        return self._env_context

    @property
    def api_url(self):
        """Create the airbrake api endpoint and returns a string."""
        if not self._api_url:
            if self.project_id and self.api_key:
                address = ("http://airbrake.io/api/v3/projects/%s/notices"
                           % self.project_id)
                if self.use_ssl:
                    api_endpoint = urlparse.urlparse(address)
                    self._api_url = api_endpoint._replace(
                        scheme="https").geturl()
                else:
                    self._api_url = address
            else:
                LOG.warning("API Key and Project ID required for airbrake.io")

        return self._api_url

    @property
    def calling_module(self):
        """Should be called from Airbrake.__init__
        Not otherwise smart enough yet.
        """
        if not self._calling_module:
            self._calling_module = inspect.stack()[2][1]
        return self._calling_module

    def log(self, exc=None, record=None, params=None):
        """Acknowledge an error, prepare it to be shipped to Airbrake,
        and append to Airbrake.errors. If Airbrake.auto_notify=True, the error
        will also be shipped to Airbrake immediately; otherwise, all
        logged errors will be shipped on the next call to Airbrake.notify().

        :param exc:    Exception instance to log.
        :param record: Log record.
        :param params: Payload field "params" which only has one definition
                       per call to notify(). It is definable here only for
                       convenience, assuming log() is the primary function
                       used in this module.
        """
        if params:
            if not isinstance(params, dict):
                LOG.warning("Unable to set `params`. "
                            "Payload 'params' should be a dictionary.")
            else:
                self.payload['params'] = params

        if exc:
            error = Airbrake.Error(self, exc=exc)

        if record:
            error = Airbrake.Error(self, record=record)

        if self.auto_notify == True:
            self.notify()
        return error

    def notify(self):
        """Post the JSON body to airbrake.io. Ships all errors aggregated by
        Airbrake.log() and resets the errors list in `errors` attribute.
        """
        if self.api_url is None:
            LOG.warning("The API endpoint has not been defined, this likely"
                        "means that proper API key and project ID have not"
                        "been provided.")
            return None

        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}

        if not self.errors:
            msg = "No errors to ship. Maybe your code isn't so bad."
            LOG.warning(msg)

        response = requests.post(self.api_url, data=json.dumps(self.payload),
                                 headers=headers, params=api_key)
        response.raise_for_status()
        del self.errors[:]
        return response.status_code

    def deploy(self, env=None):

        if env:
            environment = env
        else:
            environment = self.environment

        params = {'api_key': self.api_key,
                  'deploy[rails_env]': str(environment)}

        response = requests.post(self.deploy_url, params=params)
        response.raise_for_status()
        return response.status_code

    class Error(object):
        """Not to be used directly. This nested class formats exception
        related info to adhere to the schema defined in the airbrake.io
        documentation.

        The airbrake.io docs used to implements this class are here:
            http://help.airbrake.io/kb/api-2/notifier-api-v3
        """

        def __init__(self, manager, exc=None, record=None):

            self.manager = manager

            #default (to be overwritten)
            self.__error__ = {'type': "N/A",
                              'backtrace': [{'file': "N/A",
                                             'line': 1,
                                             'function': "N/A"}],
                              'message': "N/A"}

            if exc:
                if not isinstance(exc, Exception):
                    raise TypeError("Airbrake.Error expecting "
                                    "<type 'exceptions.Exception'> "
                                    "for keyword argument 'exc'. "
                                    "Got %s instead, of type %s."
                                    % (exc, str(type(exc))))
                else:
                    self.trace = sys.exc_info()[2]
                    self.lastline = traceback.format_exc().splitlines()[-1]
                    self.__error__.update({'type': exc.__class__.__name__,
                                           'backtrace': [],
                                           'message': self.lastline})
                    self._format_backtrace()
                    del self.trace

            if record:
                if not isinstance(record, basestring):
                    raise TypeError("Airbrake.Error expecting "
                                    "<type 'basestring'> "
                                    "for keyword argument 'record'. "
                                    "Got %s instead, of type %s."
                                    % (record, str(type(record))))
                else:
                    self.__error__.update({'type': 'Record',
                                           'message': record})

            self.manager.errors.append(self.__error__)

        def _format_backtrace(self):
            """Format backtrace dict and append to the array of errors
            managed by the Airbrake instance."""
            for filename, line, func, _ in traceback.extract_tb(self.trace):
                line = {'file': filename,
                        'line': line,
                        'function': func}
                self.__error__['backtrace'].append(line)

