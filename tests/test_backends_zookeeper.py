# pylint: disable=redefined-outer-name


from powny.backends.zookeeper import ifaces
from powny.backends import zookeeper

from .fixtures.zookeeper import zclient  # pylint: disable=unused-import
from .fixtures.zookeeper import zclient_kwargs  # pylint: disable=unused-import
from .fixtures.zookeeper import zclient_chroot  # pylint: disable=unused-import
zclient  # flake8 suppression pylint: disable=pointless-statement
zclient_kwargs  # flake8 suppression pylint: disable=pointless-statement
zclient_chroot  # flake8 suppression pylint: disable=pointless-statement


# =====
def test_connect(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs).connected():
        pass


def test_get_info(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs).connected() as backend:
        info = backend.get_info()
        assert "zookeeper.version" in info["envi"]
        assert "zk_version" in info["mntr"]


def test_ifaces(zclient_kwargs, zclient_chroot):
    with zookeeper.Backend(chroot=zclient_chroot, **zclient_kwargs).connected() as backend:
        assert isinstance(backend.jobs_control, ifaces.JobsControl)
        assert isinstance(backend.jobs_process, ifaces.JobsProcess)
        assert isinstance(backend.rules, ifaces.Rules)
        assert isinstance(backend.system_apps_state, ifaces.AppsState)
