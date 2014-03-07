import logging

from raava import zoo

from .. import zclient
from .. import env


##### Private constants #####
_STORAGE_PATH = zoo.join(zoo.USER_PATH, __name__)


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Private classes #####
class _NoValue:
    pass


##### Exceptions #####
class NoValueError(Exception):
    pass

class VersionError(Exception):
    pass


##### Private methods #####
def _replace_value(path, value=_NoValue, default=_NoValue, version=None, fatal_write=True):
    """
        _replace_value() - implementation of CAS, stores the new value if it is superior to the
        existing version. Standard kazoo set() require strict comparison and incremented
        version of the data themselves.
    """

    with zclient.get_context(env.get_config()) as client:
        path = zoo.join(_STORAGE_PATH, path)
        with client.Lock(zoo.join(path, zoo.LOCK)):
            try:
                (old_value, old_version) = client.pget(path)
            except EOFError as err:
                if default is _NoValue:
                    raise NoValueError from err
                (old_value, old_version) = (default, None)

            write_ok = None
            if value is not _NoValue:
                if version is not None and old_version is not None and version <= old_version:
                    write_ok = False
                    msg = "Can't rewrite %s with version %d (old version: %d)" % (path, version, old_version)
                    if not fatal_write:
                        _logger.debug(msg)
                    else:
                        raise VersionError(msg)
                else:
                    client.pset(path, (value, version))
                    write_ok = True
    return (old_value, old_version, write_ok)

def _set_value(path, value, version=None):
    try:
        _replace_value(path, value, None, version)
        return True
    except VersionError:
        _logger.exception("Can't set %s value with version %s", path, version)
        return False

def _get_value(path, default=_NoValue):
    return _replace_value(path, _NoValue, default)[:2]


##### Private classes #####
class _Storage:
    replace = _replace_value
    set = _set_value
    get = _get_value
    NoValueError = NoValueError
    VersionError = VersionError


##### Public constants #####
BUILTINS_MAP = {
    "storage": _Storage,
}

