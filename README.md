airbrake-python
===============

<img src="http://f.cl.ly/items/3Z1A202C1U2j3E1O1N0n/python%2009.19.32.jpg" width=800px>

Python library to export errors and exceptions to [airbrake.io](https://airbrake.io/)

Airbrake integration for python that easily plugs into your existing code.

```python
import airbrake

logger = airbrake.getLogger()

try:
    1/0
except Exception as exc:
    logger.exception("Bad math.")

```
airbrake-python is used most effectively as a [logging](http://docs.python.org/2/library/logging.html) handler

###install
```bash
pip install -U airbrake
```

###setup
```bash
export AIRBRAKE_API_KEY=*****
export AIRBRAKE_PROJECT_ID=12345
export AIRBRAKE_ENVIRONMENT=dev
```


####give your exceptions more context
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
