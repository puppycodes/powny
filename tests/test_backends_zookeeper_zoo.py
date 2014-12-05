# pylint: disable=protected-access
# pylint: disable=redefined-outer-name


import threading
import pickle
import time

import kazoo.handlers.threading
import kazoo.exceptions
import pytest

from powny.backends.zookeeper import zoo

from .fixtures.zookeeper import zclient  # pylint: disable=unused-import
from .fixtures.zookeeper import zbackend_kwargs  # pylint: disable=unused-import
zclient  # flake8 suppression pylint: disable=pointless-statement
zbackend_kwargs  # flake8 suppression pylint: disable=pointless-statement


# =====
def test_empty_value():
    with pytest.raises(RuntimeError):
        zoo.EmptyValue()


class TestEncodeValue:
    def test_encode_value(self):
        obj = ("foobar",)
        encoded = zoo._encode_value(obj)
        assert encoded == pickle.dumps(obj)

    def test_encode_value_none(self):
        encoded = zoo._encode_value(None)
        assert encoded == pickle.dumps(None)

    def test_encode_value_empty(self):
        encoded = zoo._encode_value(zoo.EmptyValue)
        assert encoded == b""


class TestDecodeValue():
    def test_decode_value(self):
        obj = ("foobar",)
        decoded = zoo._decode_value(pickle.dumps(obj))
        assert decoded == obj

    def test_decode_value_none(self):
        assert zoo._decode_value(pickle.dumps(None)) is None

    def test_decode_value_empty(self):
        assert zoo._decode_value(b"") == zoo.EmptyValue

    def test_decode_value_invalid(self):
        with pytest.raises(AssertionError):
            zoo._decode_value("foobar")


class TestCatchZk:
    def test_catch_zk_no_node_error(self):
        self._test_catch_zk_exc(kazoo.exceptions.NoNodeError, zoo.NoNodeError)

    def test_catch_zk_node_exists_error(self):
        self._test_catch_zk_exc(kazoo.exceptions.NodeExistsError, zoo.NodeExistsError)

    def test_catch_zk_runtime_error(self):
        self._test_catch_zk_exc(RuntimeError, RuntimeError)

    def test_catch_zk_ok(self):
        @zoo._catch_zk
        def method(*args, **kwargs):
            return (args, kwargs)
        args = (1, 2, 3)
        kwargs = dict.fromkeys(map(str, args))
        assert method(*args, **kwargs) == (args, kwargs)

    def _test_catch_zk_exc(self, in_exc, out_exc):
        @zoo._catch_zk
        def method():
            raise in_exc
        with pytest.raises(out_exc):
            method()


class TestClient:
    def test_connect(self, zclient):
        pass

    def test_connect_failed(self):
        with pytest.raises(kazoo.handlers.threading.TimeoutError):
            with zoo.Client(
                nodes=("unexistent.domain:2181",),
                timeout=1,
                start_timeout=3,
                start_retries=1,
                randomize_hosts=True,
                chroot=None,
            ).connected():
                pass

    def test_get_server_info(self, zclient):
        info = zclient.get_server_info()
        assert "zookeeper.version" in info["envi"]
        assert "zk_version" in info["mntr"]

    # ===

    def test_write_exception(self, zclient):
        with pytest.raises(RuntimeError):
            with zclient.make_write_request():
                raise RuntimeError

    def test_empty_write_request(self, zclient):
        with pytest.raises(AssertionError):
            with zclient.make_write_request():
                pass

    def test_create(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node", 12309)
        assert zclient.get("/test-node") == 12309

    def test_create_multi(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node-1", 0)
            request.create("/test-node-2", 1)
        assert zclient.get("/test-node-1") == 0
        assert zclient.get("/test-node-2") == 1

    def test_create_empty(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
        assert zclient.get("/test-node") == zoo.EmptyValue

    def test_create_node_exists_error(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
        with pytest.raises(zoo.NodeExistsError):
            with zclient.make_write_request() as request:
                request.create("/test-node")

    def test_create_multi_node_exists_error(self, zclient):
        with pytest.raises(zoo.NodeExistsError):
            with zclient.make_write_request() as request:
                request.create("/test-node")
                request.create("/test-node")

    def test_create_multi_middle_node_exists_error(self, zclient):
        with pytest.raises(zoo.NodeExistsError):
            with zclient.make_write_request() as request:
                request.create("/test-node")
                request.create("/test-node")
                request.create("/foobar")

    # ===

    def test_set(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
        assert zclient.get("/test-node") == zoo.EmptyValue
        with zclient.make_write_request() as request:
            request.set("/test-node", "foobar")
        assert zclient.get("/test-node") == "foobar"

    def test_set_no_node_error(self, zclient):
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                request.set("/test-node", 0)

    def test_set_multi(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
            request.set("/test-node", 0)
            request.set("/test-node", 1)
        assert zclient.get("/test-node") == 1

    def test_set_multi_no_node_error(self, zclient):
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                request.create("/test-node-2")
                request.set("/test-node-1", 0)
                request.set("/test-node-2", 0)

    # ===

    def test_delete(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
        with zclient.make_write_request() as request:
            request.delete("/test-node")

    def test_delete_no_node_error(self, zclient):
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                request.delete("/test-node")

    def test_delete_multi(self, zclient):
        with zclient.make_write_request() as request:
            for count in range(5):
                request.create("/test-node-{}".format(count))
        with zclient.make_write_request() as request:
            for count in range(5):
                request.delete("/test-node-{}".format(count))

    def test_delete_multi_no_node_error(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node-1")
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                request.delete("/test-node-1")
                request.delete("/test-node-2")

    # ===

    def test_get_children(self, zclient):
        with zclient.make_write_request() as request:
            nodes = sorted(["node-{}".format(count) for count in range(5)])
            for node in nodes:
                request.create("/" + node)
        assert sorted(zclient.get_children("/")) == nodes
        assert zclient.get_children_count("/") == len(nodes)

    def test_get_children_no_node_error(self, zclient):
        with pytest.raises(zoo.NoNodeError):
            zclient.get_children("/test-node")

    # ===

    def test_exists_true(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/test-node")
        assert zclient.exists("/test-node")

    def test_exists_false(self, zclient):
        assert not zclient.exists("/test-node")


class TestLock:
    def test_transaction(self, zclient):
        lock1 = zclient.get_lock("/lock")
        lock2 = zclient.get_lock("/lock")
        assert not lock1.is_locked()
        with zclient.make_write_request() as request:
            lock1.acquire(request)
        assert lock1.is_locked()
        with pytest.raises(zoo.NodeExistsError):
            with zclient.make_write_request() as request:
                lock2.acquire(request)
        with zclient.make_write_request() as request:
            lock1.release(request)
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                lock2.release(request)

    def test_lock_context(self, zclient):
        with zclient.make_write_request() as request:
            zclient.get_lock("/lock").acquire(request)

        def release():
            time.sleep(3)
            with zclient.make_write_request() as request:
                zclient.get_lock("/lock").release(request)

        unlocker = threading.Thread(target=release)
        unlocker.daemon = True
        unlocker.start()

        before = time.time()
        lock = zclient.get_lock("/lock")
        assert lock.is_locked()
        with zclient.get_lock("/lock"):
            assert lock.is_locked()
        assert not lock.is_locked()
        assert time.time() - before >= 3


class TestQueue:
    def test_put_no_node_error(self, zclient):
        queue = zclient.get_queue("/queue")
        with pytest.raises(zoo.NoNodeError):
            with zclient.make_write_request() as request:
                queue.put(request, None)

    def test_get_no_node_error(self, zclient):
        queue = zclient.get_queue("/queue")
        with pytest.raises(zoo.NoNodeError):
            next(iter(queue))

    def test_put_len_get_consume(self, zclient):
        with zclient.make_write_request() as request:
            request.create("/queue")
        queue = zclient.get_queue("/queue")

        for count in range(5):
            with zclient.make_write_request() as request:
                queue.put(request, count)
                queue.put(request, count * 10)

        assert len(queue) == 10

        iterator = iter(queue)
        for count in range(5):
            for factor in (1, 10):
                assert next(iterator) == count * factor
                with zclient.make_write_request() as request:
                    queue.consume(request)
        with pytest.raises(StopIteration):
            next(iterator)
