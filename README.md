<p align="center">
  <img src="https://airbrake-github-assets.s3.amazonaws.com/brand/airbrake-full-logo.png" width="200">
</p>

airbrake-python
===============

*Note*. Python 3.4+ are advised to use new [Airbrake Python notifier](https://github.com/airbrake/pybrake) which supports async API and code hunks. Python 2.7 users should continue to use this notifier.

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

### install
To install airbrake-python, run:
```bash
$ pip install -U airbrake
```

### setup
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

By default, airbrake will catch and send uncaught exceptions. To avoid this behaviour, use the send_uncaught_exc option:
`logger = airbrake.getLogger(api_key=*****, project_id=12345, send_uncaught_exc=False)`

### setup for Airbrake On-Premise and other compatible back-ends (e.g. Errbit)

Airbrake [Enterprise](https://airbrake.io/enterprise) and self-hosted alternatives, such as [Errbit](https://github.com/errbit/errbit), provide a compatible API.

You can configure a different endpoint than the default (`https://api.airbrake.io`) by either:

 * Setting an environment variable:

```bash
export AIRBRAKE_HOST=https://self-hosted.errbit.example.com/
```

 * Or passing a `host` argument to the `getLogger()` helper:

```python
import airbrake

logger = airbrake.getLogger(api_key=*****, project_id=12345, host="https://self-hosted.errbit.example.com/")
```

#### adding the AirbrakeHandler to your existing logger
```python
import logging

import airbrake

yourlogger = logging.getLogger(__name__)
yourlogger.addHandler(airbrake.AirbrakeHandler())
```
_by default, the `AirbrakeHandler` only handles logs level ERROR (40) and above_

#### Additional Options
More options are available to configure this library.

For example, you can set the environment to add more context to your errors.
One way is by setting the AIRBRAKE_ENVIRONMENT env var.
```
export AIRBRAKE_ENVIRONMENT=staging
```
Or you can set it more explicitly when you instantiate the logger.
```python
import airbrake

logger = airbrake.getLogger(api_key=*****, project_id=12345, environment='production')
```

The available options are:
- environment, defaults to env var `AIRBRAKE_ENVIRONMENT`
- host, defaults to env var `AIRBRAKE_HOST` or https://api.airbrake.io
- root_directory, defaults to None
- timeout, defaults to 5. (Number of seconds before each request times out)
- send_uncaught_exc, defaults to True (Whether or not to send uncaught exceptions)

#### giving your exceptions more context
```python
import airbrake

logger = airbrake.getLogger()

def bake(**goods):
    try:
        temp = goods['temperature']
    except KeyError as exc:
        logger.error("No temperature defined!", extra=goods)
```

#### Setting severity

[Severity][what-is-severity] allows categorizing how severe an error is. By
default, it's set to `error`. To redefine severity, simply `build_notice` with
the needed severity value. For example:

```python
notice = airbrake.build_notice(exception, severity="critical")
airbrake.notify(notice)
```

### Using this library without a logger

You can create an instance of the notifier directly, and send
errors inside exception blocks.
```python
from airbrake.notifier import Airbrake

ab = Airbrake(project_id=1234, api_key='fake')

try:
    amazing_code()
except ValueError as e:
    ab.notify(e)
except:
    # capture all other errors
    ab.capture()
```


#### Running Tests Manually
Create your environment and install the test requirements
```
virtualenv venv
source venv/bin/activate
pip install .
python setup.py test
```

To run via nose (unit/integration tests):
```
source venv/bin/activate
pip install -r ./test-requirements.txt
source venv/bin/activate
nosetests
```

Run all tests, including multi-env syntax, and coverage tests.
```
pip install tox
tox -v --recreate
```

It's suggested to make sure tox will pass, as CI runs this.
tox needs to pass before any PRs are merged.

-----------------

The [airbrake.io](https://airbrake.io/) api docs used to implement airbrake-python are here:
https://airbrake.io/docs/api/

[[what-is-severity]: https://airbrake.io/docs/airbrake-faq/what-is-severity/]
