import sys

import airbrake


def run_test():
    logger = airbrake.getLogger(environment='airbrake-python-test')

    try:
        1/0
    except ZeroDivisionError:
        logger.exception("Bad math.")

    logger.error("No exception, but something to be concerned about.")

    for handler in logger.handlers:
        if isinstance(handler, airbrake.AirbrakeHandler):
            abhandler = handler
    response = abhandler.airbrake.log(message='Finishing real test.')
    response.raise_for_status()

if __name__ == '__main__':
    run_test()
