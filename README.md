airbrake-python
===============

Python library to export errors and exceptions to Airbrake.io


As a [logging](http://docs.python.org/2/library/logging.html) handler
-----------------------------------

Auto-notify is enabled by default:

```python
     import logging
     import os
     
     import airbrake
     
     
     pid = os.environ['AIRBRAKE_PROJECT_ID']
     apikey = os.environ['AIRBRAKE_API_KEY']
     
     logger = logging.getLogger(__name__)
     ab = airbrake.AirbrakeHandler(pid, apikey, "readmenv")
     ab.setLevel(logging.DEBUG)
     logger.addHandler(ab)
     logger.setLevel(logging.DEBUG)
     
     # ab.airbrake.deploy()  # resolves errors
     
     try:
         1/0
     except Exception as exc:
         logger.exception(exc)
         
```

Or just use the module directly
------------
```python
     import os

     import airbrake
     
     
     pid = os.environ['AIRBRAKE_PROJECT_ID']
     apikey = os.environ['AIRBRAKE_API_KEY']
     
     ab = Airbrake(pid, apikey, "readmenv")

     try:
         interesting = {'field': 'TODO(sam): put better info here.',
                        'git_blame': 'N/A',
                        'netloc': 'http://app.example.com'}
         1/0
     except Exception as exc:
         ab.log(exc, params=interesting)
```



If auto-notify is disabled:

```python
     import os

     import airbrake
     
     
     pid = os.environ['AIRBRAKE_PROJECT_ID']
     apikey = os.environ['AIRBRAKE_API_KEY']
     
     ab = Airbrake(pid, apikey, "readmenv", auto_notify=False)

     try:
         interesting = {'field': 'TODO(sam): put better info here.',
                        'git_blame': 'N/A',
                        'netloc': 'http://app.example.com'}
         1/0
     except Exception as exc:
         ab.log(exc, params=interesting)

     # more code, possible errors

     ab.notify()
```

##### The params we passed to `ab.log()` end up here:  

![params](https://github.rackspace.com/bk-box/python-airbrake/raw/master/data/airbrake_params.png)


-------


The above are decent enough examples, but you'll probably want to  
include a `notifier` dictionary upon instantiating the `Airbrake` class.

* `notifier`
  * The notifier client object.
  * Describes the notifier client submitting the request.
  * Should contain `name`, `version`, and `url`. type: `dict`

-----------------

The [airbrake.io](https://airbrake.io/) docs used to implement airbrake-python are here:
http://help.airbrake.io/kb/api-2/notifier-api-v3
