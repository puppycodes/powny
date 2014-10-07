import importlib
import contextlib
import collections
import uuid
import queue

from contextlog import get_logger


# =====
class DeleteTimeoutError(Exception):
    pass


ReadyJob = collections.namedtuple("ReadyJob", (
    "job_id",
    "number",
    "version",
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

    def __init__(self, size, name, backend_opts):
        self._size = size
        self._name = name
        self._backend_opts = backend_opts
        self._backend_class = get_backend_class(name)
        self._queue = queue.Queue(self._size)
        self._backends = []
        self._filled = False

    def get_backend_name(self):
        return self._name

    @contextlib.contextmanager
    def get_backend(self):
        assert self._filled and len(self._backends) != 0, "Not filled"
        backend = self._queue.get()
        self._queue.task_done()
        try:
            yield backend
        except Exception:
            get_logger().info("Exception in the backend context, need to reopen one")
            self._close_backend(backend)
            backend = self._open_backend()
            raise
        finally:
            self._queue.put(backend)

    def __enter__(self):
        assert not self._filled, "Pool is disposable"
        for _ in range(self._queue.qsize(), self._size):
            self._queue.put(self._open_backend())
        self._filled = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert len(self._backends) != 0, "Is already free"
        for backend in list(self._backends):
            self._close_backend(backend)

    def __len__(self):
        return self._queue.qsize()  # Number of unused backends

    def _open_backend(self):
        get_logger().debug("Opening backend: %s(%s)", self._backend_class, self._backend_opts)
        backend = self._backend_class(**self._backend_opts)
        backend.open()
        self._backends.append(backend)
        return backend

    def _close_backend(self, backend):
        self._backends.remove(backend)
        try:
            backend.close()
        except Exception:
            get_logger().exception("Error while closing backend: %s", backend)
