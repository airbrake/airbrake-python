"""
    airbrake-python
    ~~~~~~~~~~~~~~~

    Client for sending python exceptions to airbrake.io
"""

__version__ = "1.1.0"
__url__ = "https://github.com/airbrake/airbrake-python"
__notifier__ = {
    'name': 'airbrake-python',
    'version': __version__,
    'url': __url__
}


from airbrake import utils
from airbrake.notifier import Airbrake
from airbrake.handler import AirbrakeHandler
