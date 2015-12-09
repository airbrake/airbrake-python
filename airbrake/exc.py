"""Airbrake-Python custom exceptions."""


class AirbrakeException(Exception):

    """Base class for errors thrown by airbrake-python."""


class AirbrakeNotConfigured(AirbrakeException):

    """The client was not given id and key nor found in env."""
