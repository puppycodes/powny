import importlib
import contextlib
import collections
import uuid
from queue import Queue

from contextlog import get_logger


# =====
class DeleteTimeoutError(Exception):
    pass


ReadyJob = collections.namedtuple("ReadyJob", (
    "job_id",
    "number",
    "head",
    "method_name",
    "state",
))


def make_job_id():
    return str(uuid.uuid4())


# =====
class CasNoValueError(Exception):
    pass


class CasVersionError(Exception):
    pass


class CasNoValue:  # Empty value for CAS-storage
    def __new__(cls):
        raise RuntimeError("Use a class rather than an object of class")


CasData = collections.namedtuple("CasData", (
    "value",
    "version",
    "stored",
))


# =====
def get_backend_class(name):
    module = importlib.import_module("powny.backends." + name)
    return getattr(module, "Backend")


class Pool:
    """
        This pool contains several ready-to-use backend objects.
        Some code that wants to use the backend, asks it from the pool.
        After using backend, it's returned to the pool. If the exception occurred,
        backend object will be removed with closing the internal connection and
        replaced to the new object.
    """

    def __init__(self, size, backend_name, backend_opts):
        self._backend_name = backend_name
        self._backend_opts = backend_opts
        self._free_backends = Queue(size)
        for _ in range(size):
            self._free_backends.put(None)

    def get_backend_name(self):
        return self._backend_name

    @contextlib.contextmanager
    def get_backend(self):
        backend = self._free_backends.get()
        self._free_backends.task_done()
        try:
            if backend is None:
                backend = self._open_backend()
            yield backend
        except Exception:
            get_logger().info("Exception in the backend context, need to reopen one")
            if backend is not None:
                self._close_backend(backend)
                backend = None
            raise
        finally:
            self._free_backends.put(backend)

    def __len__(self):
        return self._free_backends.qsize()  # Number of free backends

    def _open_backend(self):
        backend_class = get_backend_class(self._backend_name)
        get_logger().debug("Opening backend: %s(%s)", backend_class, self._backend_opts)
        backend = backend_class(**self._backend_opts)
        backend.open()
        return backend

    def _close_backend(self, backend):
        try:
            backend.close()
        except Exception:
            get_logger().exception("Error while closing backend: %s", backend)
