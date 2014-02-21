import pickle
import logging

from raava import zoo

from .. import service
from .. import env


##### Private constants #####
_USER_PATH = "/user_storage"


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Private classes #####
class _NoDefault:
    pass


##### Private methods #####
def _client_opts():
    return env.get_config(service.S_CORE, service.O_ZOO_NODES)

def _client_context():
    return zoo.Connect(_client_opts())


###
def _set_value(path, value):
    data = pickle.dumps(value)
    path = zoo.join(_USER_PATH, path)
    with _client_context() as client:
        try:
            client.create(path, data, makepath=True)
        except zoo.NodeExistsError:
            client.set(path, data)

def _get_value(path, default=_NoDefault):
    path = zoo.join(_USER_PATH, path)
    with _client_context() as client:
        try:
            result = client.pget(path)
        except (zoo.NoNodeError, EOFError):
            if default is not _NoDefault:
                result = default
            else:
                _logger.exception("Non-existent node: %s", path)
                raise
    return result


##### Private classes ####
class _Lock:
    def __init__(self, path):
        self._path = path
        self._client = None
        self._lock = None

    def __enter__(self):
        self._client = zoo.connect(_client_opts())
        self._lock = self._client.Lock(zoo.join(_USER_PATH, self._path, "lock"))
        self._lock.acquire()

    def __exit__(self, type, value, traceback): # pylint: disable=W0622
        self._lock.release()
        self._lock = None
        self._client.stop()
        self._client = None



##### Private classes #####
class _Storage:
    set = _set_value
    get = _get_value
    lock = _Lock


##### Public constants #####
BUILTINS_MAP = {
    "storage": _Storage,
}

