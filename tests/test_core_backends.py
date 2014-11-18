# pylint: disable=redefined-outer-name


import pytest

from powny.core import backends
import powny.backends.zookeeper

from .fixtures.zookeeper import zclient  # pylint: disable=unused-import
from .fixtures.zookeeper import zbackend_kwargs  # pylint: disable=unused-import
zclient  # flake8 suppression pylint: disable=pointless-statement
zbackend_kwargs  # flake8 suppression pylint: disable=pointless-statement


# =====
class TestBackends:
    def test_get_backend_zookeeper(self):
        assert backends.get_backend_class("zookeeper") == powny.backends.zookeeper.Backend

    def test_get_backend_import_error(self):
        with pytest.raises(ImportError):
            backends.get_backend_class("foobar")


@pytest.mark.usefixtures("zclient")
class TestZookeeperPool:
    def test_cycle(self, zbackend_kwargs):
        pool = backends.Pool(5, "zookeeper", zbackend_kwargs)
        assert pool.get_backend_name() == "zookeeper"
        assert len(pool) == 5
        for _ in range(5):
            with pytest.raises(RuntimeError):
                with pool.get_backend() as backend:
                    assert backend.rules.get_head() is None
                    raise RuntimeError("Close backend on exception")
