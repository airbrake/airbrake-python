import mock
import sys
import traceback
import unittest

from airbrake.notifier import format_backtrace
from airbrake.utils import is_exc_info_tuple


class FakeTraceback(object):
    def __init__(self, tb_frame, tb_lineno, tb_next):
        self.tb_frame = tb_frame
        self.tb_lineno = tb_lineno
        self.tb_next = tb_next


class TestTraceback(unittest.TestCase):
    def _exc_info(self):
        try:
            1/0
        except ZeroDivisionError as e:
            return sys.exc_info()

    def _make_fake_traceback(self, tb):
        return FakeTraceback(tb.tb_frame, tb.tb_lineno, tb.tb_next)

    def test_format(self):
        tb = self._exc_info()[2]
        fake_tb = self._make_fake_traceback(tb)
        assert format_backtrace(tb) == format_backtrace(fake_tb)

    def test_is_exc_info_tuple(self):
        exc_info = self._exc_info()
        assert is_exc_info_tuple(exc_info)
        exc_info = exc_info[0], exc_info[1], self._make_fake_traceback(exc_info[2])
        assert is_exc_info_tuple(exc_info)


if __name__ == '__main__':
    unittest.main()
