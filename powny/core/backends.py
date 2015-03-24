import importlib
import collections
import uuid
from queue import Queue
import time

from contextlog import get_logger


# =====
class DeleteTimeoutError(Exception):
    pass


JobState = collections.namedtuple("JobState", (
    "head",
    "method_name",
    "kwargs",
    "state",
    "job_id",
))


def make_job_id():
    return str(uuid.uuid4())


# =====
class ConnectionError(Exception):
    pass


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
            self._free_backends.put(self._create_backend())

    def get_backend_name(self):
        return self._backend_name

    def get_backend(self):
        backend = self._free_backends.get()
        if not backend.is_alive():
            if backend.is_opened():
                try:
                    backend.close()
                except Exception:
                    get_logger().error("Can't close backend %s", backend)
            try:
                backend.open()
            except Exception:
                get_logger().error("Can't open backend %s", backend)
                self._free_backends.put(backend)
                raise
        return backend

    def retrieve_backend(self, backend):
        self._free_backends.put(backend)

    def __len__(self):
        return self._free_backends.qsize()  # Number of free backends

    def _create_backend(self):
        backend_class = get_backend_class(self._backend_name)
        backend = backend_class(**self._backend_opts)
        get_logger().debug("Created backend: %s(%s) = %s", backend_class, self._backend_opts, backend)
        return backend


def retry(pool, method, args=(), kwargs=None, retries=5, sleep=1, stopper=None):
    kwargs = (kwargs or {})
    while retries and (stopper is None or not stopper()):
        retries -= 1
        try:
            backend = pool.get_backend()
            try:
                return method(backend, *args, **kwargs)
            finally:
                pool.retrieve_backend(backend)
        except ConnectionError:
            if retries == 0:
                raise
            time.sleep(sleep)
