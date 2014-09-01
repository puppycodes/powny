# pylint: disable=R0904
# pylint: disable=W0212
# pylint: disable=W0621


import pytest

from powny.core import backends
import powny.backends.zookeeper

from .fixtures.zookeeper import zclient  # pylint: disable=W0611
from .fixtures.zookeeper import zbackend_kwargs  # pylint: disable=W0611


# =====
class TestBackends:
    def test_get_backend_zookeeper(self):
        assert backends.get_backend("zookeeper") == powny.backends.zookeeper.Backend

    def test_get_backend_import_error(self):
        with pytest.raises(ImportError):
            backends.get_backend("foobar")


@pytest.mark.usefixtures("zclient")
class TestZookeeperPool:
    def test_fill_free(self, zbackend_kwargs):
        pool = backends.Pool(5, "zookeeper", zbackend_kwargs)
        pool.fill()
        assert len(pool) == 5
        with pytest.raises(AssertionError):
            pool.fill()
        pool.free()
        with pytest.raises(AssertionError):
            pool.free()

    def test_get_backend_name(self, zbackend_kwargs):
        with backends.Pool(1, "zookeeper", zbackend_kwargs) as pool:
            assert pool.get_backend_name() == "zookeeper"

    def test_get_backend(self, zbackend_kwargs):
        with backends.Pool(5, "zookeeper", zbackend_kwargs) as pool:
            with pool.get_backend() as backend:
                job_id = backend.jobs.control.add_job("13", "foobar", b"code", {})
                assert len(pool) == 4
            assert len(pool) == 5

            with pool.get_backend() as backend:
                job_info = backend.jobs.control.get_job_info(job_id)
                assert job_info["name"] == "foobar"
                assert len(pool) == 4
            assert len(pool) == 5

    def test_get_backend_with_exception(self, zbackend_kwargs):
        with backends.Pool(5, "zookeeper", zbackend_kwargs) as pool:
            old_backends = set(pool._backends)
            assert len(old_backends) == 5

            with pytest.raises(RuntimeError):
                with pool.get_backend() as backend:
                    assert isinstance(backend, powny.backends.zookeeper.Backend)
                    raise RuntimeError

            new_backends = set(pool._backends)
            assert len(new_backends) == 5
            assert old_backends != new_backends
            assert len(pool) == 5

    def test_get_backend_free_exception(self, zbackend_kwargs):
        with pytest.raises(RuntimeError):
            with backends.Pool(5, "zookeeper", zbackend_kwargs):
                raise RuntimeError

    def test_get_backend_close_failed(self, zbackend_kwargs):
        with backends.Pool(5, "zookeeper", zbackend_kwargs) as pool:
            with pool.get_backend() as backend:
                backend.close = None
