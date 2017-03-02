"""Airbrake notifier client module.

Initialize this class to ship errors to airbrake.io
using the log() method.
"""

import json
import os
import platform
import socket
import sys

import requests

from airbrake.__about__ import __notifier__
from airbrake import exc as ab_exc
from airbrake import utils
from airbrake.notice import Notice, Error


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

    # pylint: disable=too-many-instance-attributes

    AIRBRAKE_HOST_DEFAULT = 'https://airbrake.io'
    AIRBRAKE_TIMEOUT_DEFAULT = 5

    def __init__(self, project_id=None, api_key=None, host=None, timeout=None,
                 **config):
        """Client constructor."""
        # properties
        self._api_url = None
        self._deploy_url = None
        self._context = None
        self.notifier = __notifier__

        if not project_id:
            project_id = os.getenv('AIRBRAKE_PROJECT_ID', '')
        self.project_id = str(project_id)
        if not api_key:
            api_key = os.getenv('AIRBRAKE_API_KEY', '')
        self.api_key = str(api_key)

        if not all((self.project_id, self.api_key)):
            raise ab_exc.AirbrakeNotConfigured(
                "Airbrake API Key (api_key) and Project ID "
                "(project_id) must be set. These values "
                "may be set using the environment variables "
                "AIRBRAKE_API_KEY and AIRBRAKE_PROJECT_ID or "
                "by passing in the arguments explicitly."
            )

        if not host:
            host = os.getenv('AIRBRAKE_HOST',
                             self.AIRBRAKE_HOST_DEFAULT.strip('/'))
        self.host = str(host)

        # Context values
        environment = config.get("environment",
                                 os.getenv('AIRBRAKE_ENVIRONMENT'))
        self.environment = str(environment)

        hostname = os.getenv('HOSTNAME') or socket.gethostname()
        self.hostname = str(hostname)

        self.root_directory = config.get("root_directory")
        self.timeout = timeout or self.AIRBRAKE_TIMEOUT_DEFAULT

        self._exc_queue = utils.CheckableQueue()

    def __repr__(self):
        """Return value for the repr function."""
        return ("Airbrake(project_id=%s, api_key=*****, environment=%s)"
                % (self.project_id, self.environment))

    @property
    def context(self):
        """System, application, and user data to make more sense of errors."""
        if not self._context:
            self._context = {
                'notifier': self.notifier,
                'os': platform.platform(),
                'hostname': self.hostname,
                'language': 'Python/%s' % platform.python_version(),
                'environment': self.environment,
                'rootDirectory': self.root_directory,
            }

        return self._context

    @property
    def api_url(self):
        """Create the airbrake notice api endpoint and return a string."""
        if not self._api_url:
            self._api_url = "%s/api/v3/projects/%s/notices" % (
                self.host, self.project_id)
        return self._api_url

    @property
    def deploy_url(self):
        """Create the airbrake deploy api endpoint and return a string."""
        if not self._deploy_url:
            self._deploy_url = "%s/api/v4/projects/%s/deploys" % (
                self.host, self.project_id)
        return self._deploy_url

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
        notice = self.build_notice(error, params, session, environment)

        return self.notify(notice)

    def build_notice(self, exception, params=None, session=None,
                     environment=None):
        """Build a notice object.

        :param Error|Exception|str exception:
        :param params:
        :param session:
        :param environment:
        :return: Notice
        """

        return Notice(exception, params, session, environment, self.context,
                      self.notifier)

    def notify(self, exception):
        """Post the current errors payload body to airbrake.io.

        :param Exception|str|Notice exception:
            Notice object, string, or Exception object.
            The notification payload will ultimately be sent as a JSON-encoded
            string.
        """

        notice = exception
        payload = None

        if isinstance(exception, Notice):
            payload = notice.payload

        if isinstance(exception, str) or \
                isinstance(exception, Exception) or \
                isinstance(exception, BaseException) or \
                isinstance(exception, Error):
            notice = self.build_notice(exception)
            payload = notice.payload

        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}
        response = requests.post(
            self.api_url,
            data=json.dumps(payload, cls=utils.FailProofJSONEncoder,
                            sort_keys=True),
            headers=headers,
            params=api_key,
            timeout=self.timeout)
        response.raise_for_status()
        return response

    def deploy(self, env=None, username=None, repository=None,
               revision=None, version=None):
        """Post a deploy event to airbrake.io.

        As a side-effect, this will resolve all active error groups for this
        environment and project. Any errors that still exist will get created
        again when they recur.
        """
        payload = {"environment": env or self.environment,
                   "username": username,
                   "repository": repository,
                   "revision": revision,
                   "version": version}
        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}

        response = requests.post(self.deploy_url,
                                 data=json.dumps(
                                     payload,
                                     cls=utils.FailProofJSONEncoder,
                                     sort_keys=True),
                                 headers=headers,
                                 params=api_key,
                                 timeout=self.timeout)
        response.raise_for_status()
        return response
