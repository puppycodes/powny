# pylint: disable=redefined-outer-name


import pytest

from powny.core import backends
import powny.backends.zookeeper

from .fixtures.zookeeper import zclient  # pylint: disable=unused-import
from .fixtures.zookeeper import zbackend_kwargs  # pylint: disable=unused-import


# =====
class TestBackends:
    def test_get_backend_zookeeper(self):
        assert backends.get_backend_class("zookeeper") == powny.backends.zookeeper.Backend

    def test_get_backend_import_error(self):
        with pytest.raises(ImportError):
            backends.get_backend_class("foobar")


@pytest.mark.usefixtures("zclient")
class TestZookeeperPool:
    def test_fill_free(self, zbackend_kwargs):
        pool = backends.Pool(5, "zookeeper", zbackend_kwargs)
        pool.__enter__()
        assert len(pool) == 5
        with pytest.raises(AssertionError):
            pool.__enter__()
        pool.__exit__(None, None, None)
        with pytest.raises(AssertionError):
            pool.__exit__(None, None, None)

    def test_get_backend_name(self, zbackend_kwargs):
        with backends.Pool(1, "zookeeper", zbackend_kwargs) as pool:
            assert pool.get_backend_name() == "zookeeper"

    def test_get_backend(self, zbackend_kwargs):
        with backends.Pool(5, "zookeeper", zbackend_kwargs) as pool:
            with pool.get_backend() as backend:
                job_id = backend.jobs_control.add_job("13", "foobar", b"code", {})
                assert len(pool) == 4
            assert len(pool) == 5

            with pool.get_backend() as backend:
                job_info = backend.jobs_control.get_job_info(job_id)
                assert job_info["method"] == "foobar"
                assert len(pool) == 4
            assert len(pool) == 5

    def test_get_backend_with_exception(self, zbackend_kwargs):
        with backends.Pool(5, "zookeeper", zbackend_kwargs) as pool:
            old_backends = set(pool._backends)  # pylint: disable=protected-access
            assert len(old_backends) == 5

            with pytest.raises(RuntimeError):
                with pool.get_backend() as backend:
                    assert isinstance(backend, powny.backends.zookeeper.Backend)
                    raise RuntimeError

            new_backends = set(pool._backends)  # pylint: disable=protected-access
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
