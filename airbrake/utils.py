"""Util functions/classes for airbrake-python."""

try:
    from queue import Queue, Full, Empty
except ImportError:
    # Py2 legacy fix
    from Queue import Queue, Full, Empty

import os
import traceback
import types
import json
import subprocess

try:
    TypeType = types.TypeType
except AttributeError:
    # For >= Python 3
    TypeType = type

try:
    # For >= Python 3
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class FailProofJSONEncoder(json.JSONEncoder):
    """Uses object's representation for unsupported types."""

    def default(self, o):  # pylint: disable=E0202
        # E0202 ignored in favor of compliance with documentation:
        # https://docs.python.org/2/library/json.html#json.JSONEncoder.default
        """Return object's repr when not JSON serializable."""
        try:
            return repr(o)
        except Exception:  # pylint: disable=W0703
            return super(FailProofJSONEncoder, self).default(o)


class CheckableQueue(Queue):

    """Checkable FIFO Queue which makes room for new items."""

    def __init__(self, maxsize=1000):
        """Queue constructor."""
        Queue.__init__(self, maxsize=maxsize)

    def __contains__(self, item):
        """Check the Queue for the existence of an item."""
        try:
            # pylint: disable=not-context-manager
            with self.mutex:
                return item in self.queue
        except AttributeError:
            return item in self.queue

    def put(self, item, block=False, timeout=1):
        """Add an item to the Queue."""
        try:
            Queue.put(self, item, block=block, timeout=timeout)
        except Full:
            try:
                self.get_nowait()
            except Empty:
                pass
            self.put(item)


def is_exc_info_tuple(exc_info):
    """Determine whether 'exc_info' is an exc_info tuple.

    Note: exc_info tuple means a tuple of exception related values
    as returned by sys.exc_info().
    """
    try:
        errtype, value, tback = exc_info
        if all([x is None for x in exc_info]):
            return True
        elif all((isinstance(errtype, TypeType),
                  isinstance(value, Exception),
                  hasattr(tback, 'tb_frame'),
                  hasattr(tback, 'tb_lineno'),
                  hasattr(tback, 'tb_next'))):
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
            # pylint: disable=using-constant-test
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
    lines = [line for line in lines if str(line).lower() != 'none']
    if lines:
        return lines[-1]


def non_empty_keys(data):
    """Strip out empty keys from a dict.

    :param dict data: the dict to copy
    :return:
    """
    non_empty = {}
    for (key, val) in data.items():
        if isinstance(val, dict):
            data = non_empty_keys(val)
            if data:
                non_empty[key] = data
        elif val and val != 'None':
            non_empty[key] = val
    return non_empty


def get_local_git_revision():
    """Find the commit hash of the latest local commit."""
    rev = _git_revision_with_binary()
    if not rev:
        rev = _git_revision_from_file()
    return rev


def _git_revision_with_binary():
    """Get the latest git hash using the git binary."""
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                      stderr=DEVNULL)
        return str(rev.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_revision_from_file():
    """Get the latest git hash from file in .git/refs/heads/master."""
    path = _get_git_path()
    if os.path.exists(path):
        rev = _get_git_ref_revision(path)
        if rev is None:
            return None
        return str(rev)


def _get_git_ref_revision(path):
    """Get the latest git hash from file."""
    head_ref_path_file = os.path.join(path, "HEAD")
    if not os.path.exists(head_ref_path_file):
        return None
    with open(head_ref_path_file, 'r') as ref_path_file:
        ref = ref_path_file.read().strip()
        if 'ref:' in ref:
            ref_path = ref.partition('ref:')[-1].strip()
            rev_file = os.path.join(path, ref_path)
            if not os.path.exists(rev_file):
                return None
            with open(rev_file, 'r') as rev_file_handler:
                return rev_file_handler.read().strip()
        elif len(ref) == 40:
            return ref
        else:
            return None


def _get_git_path():
    """Get the path to the local git repo."""
    package_dir = os.path.dirname(__file__)
    root_dir = os.path.normpath(os.path.join(package_dir, os.pardir))
    return os.path.join(root_dir, '.git')
