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
airbrake-python is used most effectively through its [logging](http://docs.python.org/2/library/logging.html) handler, and uses the [Airbrake V3 API](https://airbrake.io/docs/api/) for error reporting.

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

###setup for Airbrake On-Premise and other compatible back-ends (e.g. Errbit)

Airbrake [Enterprise](https://airbrake.io/enterprise) and self-hosted alternatives, such as [Errbit](https://github.com/errbit/errbit), provide a compatible API.

You can configure a different endpoint than the default (`https://airbrake.io`) by either:

 * Setting an environment variable:
 
```bash
export AIRBRAKE_HOST=https://self-hosted.errbit.example.com/
```

 * Or passing a `host` argument to the `getLogger()` helper:

```python
import airbrake

logger = airbrake.getLogger(api_key=*****, project_id=12345, host="https://self-hosted.errbit.example.com/")
```

####adding the AirbrakeHandler to your existing logger
```python
import logging

import airbrake

yourlogger = logging.getLogger(__name__)
yourlogger.addHandler(airbrake.AirbrakeHandler())
```
_by default, the `AirbrakeHandler` only handles logs level ERROR (40) and above_

#### Additional Options
More options are available to configure this library. 

For example, you can send the hostname to add more context to your errors.  
One way is by setting the HOSTNAME env var.
```
export HOSTNAME=sassbox-101.prod.api
```
Or you can set it more explicitly when you instantiate the logger.
```python
import airbrake

logger = airbrake.getLogger(api_key=*****, project_id=12345, hostname='sassbox-101.prod.api')
```

The available options are:
- hostname, defaults to env var `HOSTNAME` or `socket.gethostname()`
- environment, defaults to env var `AIRBRAKE_ENVIRONMENT`
- component, defaults to None
- action, defaults to None
- user_agent, defaults to None
- host, defaults to env var `AIRBRAKE_HOST` or https://airbrake.io
- root_directory, defaults to None
- user_id, defaults to None
- user_name, defaults to None
- user_email, defaults to None
More information about these options are available at: https://airbrake.io/docs/api/#create-notice-v3

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

The [airbrake.io](https://airbrake.io/) api docs used to implement airbrake-python are here:
https://airbrake.io/docs/api/
