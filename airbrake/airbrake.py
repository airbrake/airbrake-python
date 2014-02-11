"""Airbrake object to handle airbrake.io reporting."""
from __future__ import print_function

import json
import logging
import os
import sys
import traceback
import urlparse

import requests

LOG = logging.getLogger(__name__)


class Airbrake(object):

    """
    Class to handle exceptions that need to be sent to airbrake.io.

    The Airbrake docs used to implements this class are here:
        http://help.airbrake.io/kb/api-2/notifier-api-v3

    Usage:
        import airbrake
        ab = Airbrake(project_id="1234", api_key="1234")

        try:
            1/0
        except Exception as exn:
            ab.notify(exn)

    """

    def __init__(self, project_id=None, api_key=None,
                 environment="dev", use_ssl=True):
        if isinstance(project_id, int):
            project_id = str(project_id)

        self.project_id = project_id
        self.api_key = api_key
        self.use_ssl = use_ssl
        self.api_url = self.ab_url()
        self.environment = environment
        self.app_url = "http://app.example.com"
        self.err = {'context': {},
                    'params': {},
                    'errors': [],
                    'notifier': {},
                    'environment': {},
                    'session': {}}

    def ab_url(self):
        """Create the airbrake api endpoint and returns a string."""
        if self.project_id and self.api_key:
            url = "http://airbrake.io/api/v3/projects/%s/notices" % (
                  self.project_id
            )

            if self.use_ssl:
                api_endpoint = urlparse.urlparse(url)
                return api_endpoint._replace(scheme="https").geturl()

            return url

        LOG.warning("API Key and Project ID required for airbrake.io")

    def generate_err(self, exn):
        """Generate the error for airbrake."""
        _, _, trace = sys.exc_info()

        self.err['context'].update({'environment': self.environment})
        self.err['notifier'] = {'name': 'waldo_airbrake',
                                'version': '1.0.0',
                                'url': self.app_url
                                }

        self.err['errors'] = []

        error = {'type': exn.__class__.__name__,
                 'message': str(exn)
                 }

        error['backtrace'] = []
        for file_name, number, function_name, _ in traceback.extract_tb(trace):
            line = {'file': os.path.abspath(file_name),
                    'line': number,
                    'function': function_name
                    }
            error['backtrace'].append(line)

        self.err['errors'].append(error)

    def notify(self, exn):
        """Post the JSON body to airbrake.io."""
        if self.api_url is None:
            LOG.warning("The API endpoint has not been defined, this likely"
                        "means that proper API key and project ID have not"
                        "been provided.")
            return None
        self.generate_err(exn)

        headers = {'Content-Type': 'application/json'}
        api_key = {'key': self.api_key}

        response = requests.post(self.api_url, data=json.dumps(self.err),
                                 headers=headers, params=api_key)
        response.raise_for_status()
