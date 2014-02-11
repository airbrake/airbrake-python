airbrake-python
===============

Python library to export errors and exceptions to Airbrake.io

Usage
=====

Auto-notify is enabled by default:

     import airbrake
     ab = Airbrake(project_id="1234", api_key="1234")

     try:
         1/0
     except Exception as exc:
         ab.log(exc)

If auto-notify is disabled:

     import airbrake
     ab = Airbrake(project_id="1234", api_key="1234", auto_notify=False)

     try:
         1/0
     except Exception as exc:
         ab.log(exc)

     # more code, possible errors

     ab.notify()

The above are decent enough examples, but you'll probably want
to include a `notifier` dictionary upon instantiating Airbrake.

:param notifier: The notifier client. Describes the notifier
                 client submitting the request.
                 Should contain 'name', 'version', and 'url'
:type notifier: dict

The airbrake.io docs used to implements this class are here:
http://help.airbrake.io/kb/api-2/notifier-api-v3
