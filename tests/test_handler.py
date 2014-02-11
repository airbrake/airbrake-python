import logging
import os

import airbrake

PROJECT_ID = os.environ['AIRBRAKE_PROJECT_ID']
API_KEY = os.environ['AIRBRAKE_API_KEY']


LOG = logging.getLogger(__name__)
ab = airbrake.AirbrakeHandler(PROJECT_ID, API_KEY, "sam-test-handler")
#ab.airbrake.deploy()
ab.setLevel(logging.DEBUG)
LOG.addHandler(ab)
LOG.setLevel(logging.DEBUG)

def foo():
    log_exception()
    log_debug()


def log_exception():
    try:
        d = {}
        d['no']
    except Exception as e:
        LOG.exception(e)


def log_debug():
    LOG.debug("I am a DEBUG logging message.")

def main():
    foo()


if __name__ == '__main__':

    # multiple fn calls to generate traceback
    main()
