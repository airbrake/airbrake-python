import logging

from airbrake import Airbrake

class AirbrakeHandler(logging.Handler):
    """
    A handler class which ships logs to airbrake.io

    Requires one:
        * `project_id` AND `api_key`
        * an instance of airbrake.Airbrake
    """
    def __init__(self, airbrake=None, project_id=None, api_key=None,
                 environment="dev", notifier=None, use_ssl=True):

        logging.Handler.__init__(self)

        if isinstance(airbrake, Airbrake):
            airbrake.auto_notify = False
            self.airbrake = airbrake
        else:
            self.airbrake = Airbrake(project_id=project_id, api_key=api_key,
                                     environment=environment, notifier=notifier,
                                     use_ssl=use_ssl)

    def emit(self, record):
        try:
            self.airbrake.log(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
