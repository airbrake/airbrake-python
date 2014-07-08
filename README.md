airbrake-python
===============

<img src="http://f.cl.ly/items/3Z1A202C1U2j3E1O1N0n/python%2009.19.32.jpg" width=800px>

[Airbrake](https://airbrake.io/) integration for python that quickly and easily plugs into your existing code.

```python
import airbrake

logger = airbrake.getLogger()

try:
    1/0
except Exception:
    logger.exception("Bad math.")

```
airbrake-python is used most effectively as a [logging](http://docs.python.org/2/library/logging.html) handler, and uses the [Airbrake V3 API](https://help.airbrake.io/kb/api-2/notifier-api-v3) for error reporting.

###install
To install airbrake-python, run:
```bash
$ pip install -U airbrake
```

###setup
The easiest way to get set up is with a few environment variables:
```bash
export AIRBRAKE_API_KEY=*****
export AIRBRAKE_PROJECT_ID=12345
export AIRBRAKE_ENVIRONMENT=dev
```
and you're done!  


Otherwise, you can instantiate your `AirbrakeHandler` by passing these values as arguments to the `getLogger()` helper:
```python
import airbrake

logger = airbrake.getLogger(api_key=*****, project_id=12345)

try:
    1/0
except Exception:
    logger.exception("Bad math.")
```

####adding the AirbrakeHandler to your existing logger
```python
import logging

import airbrake

yourlogger = logging.getLogger(__name__)
yourlogger.addHandler(airbrake.AirbrakeHandler())
```
_by default, the `AirbrakeHandler` only handles logs level ERROR (40) and above_

####giving your exceptions more context
```python
import airbrake

logger = airbrake.getLogger()

def bake(**goods):
    try:
        temp = goods['temperature']
    except KeyError as exc:
        logger.error("No temperature defined!", extra=goods)
```

-----------------

The [airbrake.io](https://airbrake.io/) docs used to implement airbrake-python are here:
http://help.airbrake.io/kb/api-2/notifier-api-v3
