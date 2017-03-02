import unittest
import sys

from airbrake.notice import Notice, Error, format_backtrace
from airbrake.utils import pytb_lastline


class TestNotice(unittest.TestCase):
    def setUp(self):
        super(TestNotice, self).setUp()

    def test_create_notice_str(self):
        exception_str = "This is a test"
        exception_type = 'Error'
        notice = Notice(exception_str)

        expected_payload = {
            'errors': [{'backtrace': [{'function': 'N/A',
                                       'line': 1,
                                       'file': 'N/A'}],
                        'message': exception_str,
                        'type': exception_type}],
        }
        self.assertEqual(expected_payload, notice.payload)

    def test_create_notice_exception(self):
        exception_str = "This is a test"
        exception = ValueError(exception_str)
        exception_type = type(exception).__name__
        notice = Notice(exception)

        expected_payload = {
            'errors': [{'backtrace': [{'function': 'N/A',
                                       'line': 1,
                                       'file': 'N/A'}],
                        'message': exception_str,
                        'type': exception_type}],
        }
        self.assertEqual(expected_payload, notice.payload)

    def test_create_notice_error(self):
        try:
            raise TypeError
        except:
            exc_info = sys.exc_info()
            error = Error(exc_info=exc_info)
            notice = Notice(error)

            data = {
                'type': exc_info[1].__class__.__name__,
                'backtrace': format_backtrace(exc_info[2]),
                'message': pytb_lastline(exc_info)
            }

            expected_payload = {
                'errors': [data]
            }

            self.assertEqual(expected_payload, notice.payload)

    def test_payload_no_empty_keys(self):
        exception = Exception("This is a test")
        notice = Notice(exception, session=None)

        self.assertTrue("session" not in notice.payload)
