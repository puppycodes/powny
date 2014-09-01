# pylint: disable=R0904
# pylint: disable=W0212
# pylint: disable=W0621


from powny.backends.zookeeper import scheme
from powny.backends import zookeeper

from .fixtures.zookeeper import zclient  # pylint: disable=W0611
from .fixtures.zookeeper import zclient_kwargs  # pylint: disable=W0611
from .fixtures.zookeeper import zclient_chroot  # pylint: disable=W0611


# =====
def test_connect(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs):
        pass


def test_get_info(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs) as backend:
        assert "zookeeper.version" in backend.get_info()


def test_schemes(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs) as backend:
        assert isinstance(backend.jobs.control, scheme.JobsControlScheme)
        assert isinstance(backend.jobs.process, scheme.JobsProcessScheme)
        assert isinstance(backend.rules, scheme.RulesScheme)
        assert isinstance(backend.system.apps_state, scheme.AppsStateScheme)
