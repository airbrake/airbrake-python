"""airbrake-python.

Python SDK for airbrake.io
"""

# pylint: disable=wildcard-import

import inspect
import logging
import os

from airbrake.__about__ import *  # noqa
from airbrake import exc  # noqa
from airbrake.notifier import Airbrake  # noqa
from airbrake.handler import AirbrakeHandler  # noqa


def getLogger(name=None, **kwargs):  # pylint: disable=invalid-name
    """Return a Logger with an AirbrakeHandler."""
    if not name:
        curframe = inspect.currentframe()
        callingpath = inspect.getouterframes(curframe, 2)[1][1]
        name = os.path.split(
            callingpath.rpartition('.')[0] or callingpath)[-1]
        name = "%s%s" % ('airbrake-python-', name)
    logger = logging.getLogger(name)

    if not has_airbrake_handler(logger):
        abh = AirbrakeHandler(**kwargs)
        logger.addHandler(abh)
        if logger.getEffectiveLevel() == logging.NOTSET:
            logger.setLevel(abh.level)
        elif not logger.isEnabledFor(abh.level):
            logger.setLevel(abh.level)

    return logger


def has_airbrake_handler(logger):
    """Check a logger for an AirbrakeHandler."""
    return any([isinstance(handler, AirbrakeHandler)
                for handler in logger.handlers])
