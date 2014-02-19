import pickle
import logging

from raava import zoo
from raava import worker

from .. import service
from .. import env


##### Public constants #####
LOGGER_NAME = "user-storage"


##### Private constants #####
_USER_PATH = "/user_storage"


##### Private objects #####
_logger = logging.getLogger(LOGGER_NAME)


##### Private classes #####
class _NoDefault:
    pass


##### Private methods #####
def _client_context():
    return zoo.Connect(env.get_config(service.S_CORE, service.O_ZOO_NODES))

def _set_value(task, path, value):
    task.checkpoint()
    data = pickle.dumps(value)
    path = zoo.join(_USER_PATH, path)
    with _client_context() as client:
        try:
            client.create(path, data, makepath=True)
        except zoo.NodeExistsError:
            client.set(path, data)
    del client
    task.checkpoint()

def _get_value(task, path, default=_NoDefault):
    task.checkpoint()
    path = zoo.join(_USER_PATH, path)
    with _client_context() as client:
        try:
            result = client.pget(path)
        except zoo.NoNodeError:
            if default is not _NoDefault:
                result = default
            else:
                _logger.exception("Non-existent node: %s", path)
                raise
    del client
    task.checkpoint()
    return result


##### Private classes #####
class _Storage:
    set = worker.make_task_builtin(_set_value)
    get = worker.make_task_builtin(_get_value)


##### Public constants #####
BUILTINS_MAP = {
    "storage": _Storage,
}

