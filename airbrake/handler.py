import logging
import sys

from airbrake import Airbrake

class AirbrakeHandler(logging.Handler):
    """
    A handler class which ships logs to airbrake.io

    Requires one:
        * `project_id` AND `api_key`
        * an instance of airbrake.Airbrake
    """
    def __init__(self, project_id=None, api_key=None, environment="dev",
                 notifier=None, use_ssl=True, airbrake=None):

        logging.Handler.__init__(self)

        if isinstance(airbrake, Airbrake):
            airbrake.auto_notify = True
            self.airbrake = airbrake
        else:
            self.airbrake = Airbrake(project_id=project_id, api_key=api_key,
                                     environment=environment, notifier=notifier,
                                     use_ssl=use_ssl, auto_notify=True)

    def emit(self, record):
        try:
            # exception
            exc = None
            if record.exc_info:
                exc = record.exc_info[1]
            if not exc:
                exc = sys.exc_info()[1]
            if exc:
                self.airbrake.log(exc=exc)
                return

            # record
            record = record.getMessage()
            if record:
                self.airbrake.log(record=record)

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
