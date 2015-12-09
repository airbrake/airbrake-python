
import airbrake


def find_ab_handler(logger):
    """Return the AirbrakeHandler from logger's handlers."""
    for handler in logger.handlers:
        if isinstance(handler, airbrake.AirbrakeHandler):
            return handler


def run_test():
    """Run."""
    logger = airbrake.getLogger(environment='airbrake-python-test')
    abhandler = find_ab_handler(logger)
    # abhandler.airbrake.deploy()

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Bad math.")

    try:
        undefined  # noqa
    except Exception:
        logger.exception(
            "Undefined things!",
            extra={'additional': 'context', 'key1': 'val1'}
        )

    logger.error("No exception, but something to be concerned about.")

    abhandler = find_ab_handler(logger)
    response = abhandler.airbrake.log(message='Finishing real test.')
    response.raise_for_status()

if __name__ == '__main__':
    run_test()
