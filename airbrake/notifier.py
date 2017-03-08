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
    KEYS_TO_FILTER = ["params", "environment", "session"]
    REDACTED_DATA_MSG = '[Filtered]'

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

        self.local_revision = utils.get_local_git_revision()

        self.whitelist_keys = config.get("whitelist_keys", [])
        self.blacklist_keys = config.get("blacklist_keys", [])
        self.filter_chain = [self.filter_whitelist, self.filter_blacklist]

        self.send_env_vars = config.get("send_env_vars", False)

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

    def capture(self, exc_info=None, message=None, filename=None,
                line=None, function=None, errtype=None, **params):
        """Capture the most recent exception and send to airbrake."""
        if not utils.is_exc_info_tuple(exc_info) or not exc_info:
            exc_info = sys.exc_info()
            raw_frames = traceback.extract_tb(exc_info[2])
            exc_frame = raw_frames[0]
        err = Error(exc_info=exc_info,
                    filename=filename or str(exc_frame[0]),
                    line=line or str(exc_frame[1]),
                    function=function or str(exc_frame[2]),
                    message=message or str(exc_frame[3]),
                    errtype=errtype or "ERROR:%s" % str(exc_frame[0]),
                    **params)
        notice = self.build_notice(err)
        self.notify(notice)

    def filter_keys(self, data, key_list, filter_in_list=True):
        """
        Replace values for some keys in the data with REDACTED_DATA_MSG.

        :param dict data: Filter data from this object
        :param key_list: A list of keys to filter. Values are replaced with
            REDACTED_DATA_MSG
        :param filter_in_list: True means the key_list is a whitelist,
            otherwise it's a blacklist
        :return:
        """
        if not key_list:
            return data
        for (key, val) in data.items():
            if isinstance(val, dict):
                data = self.filter_keys(val, key_list, filter_in_list)
            elif filter_in_list and key not in key_list:
                data[key] = self.REDACTED_DATA_MSG
            elif not filter_in_list and key in key_list:
                data[key] = self.REDACTED_DATA_MSG

        return data

    def filter_whitelist(self, data):
        """Whitelist keys in data."""
        return self.filter_keys(data, self.whitelist_keys, True)

    def filter_blacklist(self, data):
        """Blacklist keys in data."""
        return self.filter_keys(data, self.blacklist_keys, False)

    def apply_filters(self, payload):
        """Filter out sensitive data in the payload.

        Applyies all filters in the filter_chain to the payload. This only
        applies to keys in KEYS_TO_FILTER.

        :param dict payload: A dict of data, typically a notice payload
        :return: dict: A filtered dict object
        """

        for key in self.KEYS_TO_FILTER:
            if key not in payload:
                continue
            for payload_filter in self.filter_chain:
                payload[key] = payload_filter(payload[key])

        return payload

    def build_notice(self, exception, params=None, session=None,
                     environment=None):
        """Build a notice object with data from this notifier instance.

        This data includes the context and notifier information

        :param Error|Exception|str exception: An exception to send to Airbrake.
        :param dict params: A dict of params to send in notice payload.
        :param dict session: A dict of session data to send in notice payload.
        :param dict environment: A dict of env vars to send in notice payload.
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

        if self.send_env_vars:
            if 'environment' not in payload:
                payload['environment'] = {}
            payload['environment'].update(os.environ)

        payload = self.apply_filters(payload)

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
        if not revision and self.local_revision:
            revision = self.local_revision
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
