"""Util functions/classes for airbrake-python."""
import Queue
import traceback
import types


class CheckableQueue(Queue.Queue):

    """Checkable FIFO Queue which makes room for new items."""

    def __init__(self, maxsize=1000):
        Queue.Queue.__init__(self, maxsize=maxsize)

    def __contains__(self, item):
        with self.mutex:
            return item in self.queue

    def put(self, item, block=False, timeout=1):
        try:
            Queue.Queue.put(self, item, block=block, timeout=timeout)
        except Queue.Full:
            try:
                self.get_nowait()
            except Queue.Empty:
                pass
            self.put(item)


def is_exc_info_tuple(exc_info):
    """Determine whether 'exc_info' is an exc_info tuple.

    Note: exc_info tuple means a tuple of exception related values
    as returned by sys.exc_info().
    """
    try:
        errtype, value, tback = exc_info
        if all(map(lambda x: x is None, exc_info)):
            return True
        elif all((isinstance(errtype, types.TypeType),
                  isinstance(value, Exception),
                  isinstance(tback, types.TracebackType))):
            return True
    except (TypeError, ValueError):
        pass
    return False


def pytb_lastline(excinfo=None):
    """Return the actual last line of the (current) traceback.

    To provide exc_info, rather than allowing this function
    to read the stack frame automatically, this function
    may be called like so:

        ll = pytb_lastline(sys.exc_info())

    OR
        try:
            1/0
        except Exception as err:
            ll = pytb_lastline(err)
    """
    lines = None
    if excinfo:
        if isinstance(excinfo, Exception):
            kls = getattr(excinfo, '__class__', '')
            if kls:
                kls = str(getattr(kls, '__name__', ''))
                kls = ("%s: " % kls) if kls else ''
            lines = [kls + str(excinfo)]
        else:
            try:
                lines = traceback.format_exception(*excinfo)
                lines = "\n".join(lines).split('\n')
            except (TypeError, AttributeError) as err:
                err.message = (
                    "Incorrect argument(s) [%s] passed to pytb_lastline(). "
                    "Should be sys.exc_info() or equivalent. | %s"
                    % (excinfo, err.message))
                raise err.__class__(err.message)
    if not lines:
        # uses sys.exc_info()
        lines = traceback.format_exc().split('\n')
    # strip whitespace, Falsy values,
    # and the string 'None', sometimes returned by the traceback module
    lines = [line.strip() for line in lines if line]
    lines = filter(lambda line: str(line).lower() != 'none', lines)
    if lines:
        return lines[-1]
