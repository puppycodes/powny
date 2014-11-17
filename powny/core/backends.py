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
        self._size = size
        self._backend_name = backend_name
        self._backend_opts = backend_opts
        self._backends = None
        self._queue = None

    def get_backend_name(self):
        return self._backend_name

    @contextlib.contextmanager
    def get_backend(self):
        assert self._queue is not None, "Not filled"
        index = self._queue.get()
        backend = self._backends[index]
        self._queue.task_done()
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
            self._backends[index] = backend
            self._queue.put(index)

    def __len__(self):
        return self._queue.qsize()  # Number of unused backends

    def __enter__(self):
        assert self._queue is None, "Pool is disposable"
        backends = []
        queue = Queue(self._size)
        for index in range(self._size):
            backends.append(None)
            queue.put(index)
        self._backends = backends
        self._queue = queue
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert self._queue is not None, "Is already free"
        self._queue = None
        for backend in list(self._backends):
            self._close_backend(backend)
        self._backends = None

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
