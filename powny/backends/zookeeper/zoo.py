import pickle
import threading
import contextlib
import re

from ...core import optconf

import decorator
import kazoo.client
import kazoo.exceptions
from kazoo.protocol.paths import join

from contextlog import get_logger


# =====
class NoNodeError(Exception):
    pass


class NodeExistsError(Exception):
    pass


class EmptyValue:  # pylint: disable=no-init
    def __new__(cls):
        raise RuntimeError("Use a class rather than an object of class")


# ====
def _encode_value(value):
    if value is EmptyValue:
        return b""
    else:
        return pickle.dumps(value)


def _decode_value(value):
    assert isinstance(value, bytes), "Invalid ZK output value type: {}".format(type(value))
    if len(value) == 0:
        return EmptyValue
    else:
        return pickle.loads(value)


def _catch_zk(method):
    def wrap(method, *args, **kwargs):
        try:
            return method(*args, **kwargs)
        except kazoo.exceptions.NoNodeError:
            raise NoNodeError
        except kazoo.exceptions.NodeExistsError:
            raise NodeExistsError
    return decorator.decorator(wrap, method)


# ====
class Client:
    """
        This interface provides a simple low-level abstraction for ZooKeeper (using kazoo),
        with a friendly interface and the logged write operations.
    """

    def __init__(self, nodes, timeout, start_timeout, start_retries, randomize_hosts, chroot):
        assert isinstance(nodes, (list, tuple))
        for node in nodes:
            assert re.match(r"[^:]+:\d+", node) is not None, "zookeeper node should has format host:port"
        self._hosts = ",".join(nodes)
        self._timeout = timeout
        self._start_timeout = start_timeout
        self._start_retries = start_retries
        self._randomize_hosts = randomize_hosts
        self._chroot = chroot
        self.zk = None

    @classmethod
    def get_options(cls):
        return {
            "nodes": optconf.Option(default=["localhost:2181"], help="List of hosts to connect (in host:port format)"),
            "timeout": optconf.Option(default=10.0, help="The longest to wait for a Zookeeper connection"),
            "start_timeout": optconf.Option(default=10.0, help="Timeout of the initial connection"),
            "start_retries": optconf.Option(default=1, type=int, help="The number of attempts the initial "
                                                                      "connection to ZooKeeper (0=infinite)"),
            "randomize_hosts": optconf.Option(default=True, help="Randomize host selection"),
            "chroot": optconf.Option(default=None, help="Use specified node as root (it must be created manually)"),
        }

    @contextlib.contextmanager
    def connected(self):
        self.open()
        try:
            yield self
        finally:
            self.close()

    def _ensure_chroot(self):
        with Client(
            nodes=self._hosts.split(","),
            timeout=self._timeout,
            start_timeout=self._start_timeout,
            start_retries=self._start_retries,
            randomize_hosts=self._randomize_hosts,
            chroot=None,
        ).connected() as client:
            try:
                with client.make_write_request("ensure_chroot()") as request:
                    request.create(self._chroot, recursive=True)
            except NodeExistsError:
                pass

    def open(self):
        if self._chroot is not None:
            self._ensure_chroot()

        self.zk = kazoo.client.KazooClient(
            hosts=self._hosts,
            timeout=self._timeout,
            randomize_hosts=self._randomize_hosts,
            command_retry={"max_delay": 60},
        )
        if self._chroot is not None:
            self.zk.chroot = self._chroot

        logger = get_logger()

        start_retries = self._start_retries
        while True:
            remaining = ("inf" if start_retries is None else start_retries)
            logger.debug("Trying to connect to ZK, attempts remaining: %s (timeout: %d)",
                         remaining, self._start_timeout, hosts=self._hosts)
            try:
                self.zk.start(timeout=self._start_timeout)
                break
            except Exception:
                logger.exception("Can't connect to ZK in this time")
                if start_retries is not None:
                    if start_retries > 0:
                        start_retries -= 1
                    else:
                        raise
        logger.debug("Started ZK client", hosts=self._hosts)

    def close(self):
        assert self.zk is not None, "Can't close() not opened client"
        self.zk.stop()
        self.zk.close()
        self.zk = None
        get_logger().debug("ZK client has been closed", hosts=self._hosts)

    def is_opened(self):
        return (self.zk is not None)

    def is_alive(self):
        return (False if self.zk is None else self.zk.connected)

    # ===

    def get_server_info(self):
        # http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_zkCommands
        return {
            "envi": self._get_info_envi(),
            "mntr": self._get_info_mntr(),
        }

    def _get_info_envi(self):
        # $ echo envi | netcat 127.0.0.1 2181
        # Environment:
        # zookeeper.version=3.4.6-1569965, built on 02/20/2014 09:09 GMT
        # host.name=localhost.localdomain
        # ...
        return dict(
            item.split("=", 1)
            for item in self.zk.command(b"envi").split("\n")[1:-1]
        )

    def _get_info_mntr(self):
        # $ echo mntr | netcat 127.0.0.1 2181
        # zk_version      3.4.6-1569965, built on 02/20/2014 09:09 GMT
        # zk_avg_latency  0
        # ...
        return dict(
            item.split("\t", 1)
            for item in self.zk.command(b"mntr").split("\n")[:-1]
        )

    # ===

    @_catch_zk
    def get_children(self, path):
        return self.zk.get_children(path)

    @_catch_zk
    def get_children_count(self, path):
        stat = self.zk.retry(self.zk.get, path)[1]
        return stat.children_count

    @_catch_zk
    def exists(self, path, watch=None):
        return (self.zk.exists(path, watch=watch) is not None)

    def get(self, path, default=EmptyValue):
        try:
            return _decode_value(self.zk.get(path)[0])
        except kazoo.exceptions.NoNodeError:
            if default is EmptyValue:
                raise NoNodeError
            return default

    def make_write_request(self, comment="<unnamed>"):
        return _WriteRequest(self, comment)

    # ===

    def get_lock(self, path, comment="<unnamed>"):
        return _Lock(self, path, comment)

    def get_queue(self, path):
        return _Queue(self, path)


class _WriteRequest:
    """
        This class is used to perform write operations in a single context.
        For several operations, the transaction is automatically used.
    """

    def __init__(self, client, comment):
        self._client = client
        self._comment = comment
        self._ops = []

    def create(self, path, value=EmptyValue, ephemeral=False, sequence=False, recursive=False):
        kwargs = {
            "path":      path,
            "value":     _encode_value(value),
            "ephemeral": ephemeral,
            "sequence":  sequence,
        }
        if recursive:
            kwargs["makepath"] = True  # XXX: Only for a single operation!
        self._ops.append(("create", kwargs))

    def set(self, path, value=EmptyValue):
        self._ops.append(("set", {
            "path":  path,
            "value": _encode_value(value),
        }))

    def delete(self, path, recursive=False):
        kwargs = {"path": path}
        if recursive:
            kwargs["recursive"] = True  # XXX: Only for a single operation!
        self._ops.append(("delete", kwargs))

    def __enter__(self):
        get_logger().debug("Created write-request", comment=self._comment)
        return self

    @_catch_zk  # for "len(self._ops) == 1"
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is not None:
            raise exc_value
        assert len(self._ops) > 0, "_WriteRequest() does not contain operations"
        if len(self._ops) == 1:
            (op_name, kwargs) = self._ops[0]
            getattr(self._client.zk, op_name)(**kwargs)
        else:
            trans = self._client.zk.transaction()
            for (op_name, kwargs) in self._ops:
                if op_name == "set":
                    op_name = "set_data"
                getattr(trans, op_name)(**kwargs)
            results = trans.commit()
            need_err = False
            for result in reversed(results):
                if isinstance(result, kazoo.exceptions.RuntimeInconsistency):
                    need_err = True
                    continue
                elif isinstance(result, Exception):
                    raise result
            assert not need_err, "No other exceptions, but runtime is inconsistent: {}".format(results)
        get_logger().debug("Completed write-request", comment=self._comment)


# =====
class _Lock:
    """
        Easy lock primitive with no queue of those who try to acqurie it.
        It can be acquired and released in the transaction.
    """

    def __init__(self, client, path, comment):
        self._client = client
        self._path = path
        self._comment = comment

    def is_locked(self):
        return (self._client.zk.exists(self._path) is not None)

    def acquire(self, request, value=EmptyValue):
        request.create(self._path, value, ephemeral=True)

    def release(self, request):
        request.delete(self._path)

    def __enter__(self):
        get_logger().debug("Acquiring lock", comment=self._comment)
        while not self._try_acquire():
            wait = threading.Event()
            if self._client.zk.exists(self._path, watch=lambda _: wait.set()) is not None:
                wait.wait()

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._client.zk.delete(self._path)
        except kazoo.exceptions.NoNodeError:
            pass
        get_logger().debug("Released lock", comment=self._comment)

    def _try_acquire(self):
        try:
            self._client.zk.create(self._path, ephemeral=True)
            return True
        except kazoo.exceptions.NodeExistsError:
            return False


class _Queue:
    """
        The queue primitive.
        This class based on the official queue recipe:
            https://zookeeper.apache.org/doc/r3.1.2/recipes.html#sc_recipes_Queues
        Our implementation does not save items order on failure (when consume() has not been called).
        This behaviour is acceptable for Powny.
    """

    def __init__(self, client, path):
        self._client = client
        self._path = path
        self._children = []
        self._last = None

    def put(self, request, value):
        assert isinstance(request, _WriteRequest), "Required _WriteRequest() object or None"
        assert not isinstance(value, EmptyValue), "Why do you need a queue for the EmptyValue?"
        path = join(self._path, "entry-")
        request.create(path, value, sequence=True)

    def __iter__(self):
        return self

    def __next__(self):
        # FIXME: need children watcher
        if self._last is not None:
            self._children.pop(0)
            self._last = None

        while True:
            if len(self._children) == 0:
                try:
                    self._children = self._client.zk.retry(self._client.zk.get_children, self._path)  # FIXME: retry?
                except kazoo.exceptions.NoNodeError:
                    raise NoNodeError
                self._children = list(sorted(self._children))
            if len(self._children) == 0:
                raise StopIteration

            name = self._children[0]
            path = join(self._path, name)
            try:
                self._client.zk.create(join(path, "__lock__"), ephemeral=True)
            except (kazoo.exceptions.NoNodeError, kazoo.exceptions.NodeExistsError):
                self._children.pop(0)  # FIXME: need a watcher
                continue
            self._last = name

            return _decode_value(self._client.zk.get(path)[0])

    def consume(self, request):
        request.delete(join(self._path, self._last, "__lock__"))
        request.delete(join(self._path, self._last))

    def __len__(self):
        return self._client.get_children_count(self._path)
