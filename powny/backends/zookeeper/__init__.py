import contextlib

from ulib.validators.common import (
    valid_number,
    valid_bool,
    valid_maybe_empty,
    valid_string_list,
)

from ...core import optconf

from . import zoo
from . import ifaces


# =====
def _valid_float_min_01(arg):
    return valid_number(arg, 0.1, value_type=float)

def _valid_number_min_1(arg):
    return valid_number(arg, 1)

def _valid_float_min_1_or_none(arg):
    return valid_maybe_empty(arg, _valid_number_min_1)

def _valid_str_or_none(arg):
    return valid_maybe_empty(arg, str)


class Backend:
    """
        ZooKeeper backend provides some interfaces for working with jobs and other operations.
        Each instance of this class contains an own connection to ZooKeeper and can be used for
        any operation.
    """

    def __init__(self, **zoo_kwargs):
        self._client = zoo.Client(**zoo_kwargs)
        self.jobs_control = ifaces.JobsControl(self._client)  # Interface for API
        self.jobs_process = ifaces.JobsProcess(self._client)  # Interface for Worker
        self.jobs_gc = ifaces.JobsGc(self._client)  # Interface for Collector
        self.rules = ifaces.Rules(self._client)  # API and internal interface to control the rules
        self.system_apps_state = ifaces.AppsState(self._client)  # API and internal interface to the system statistics

    @classmethod
    def get_options(cls):
        return {
            "nodes": optconf.Option(
                default=["localhost"], type=valid_string_list,
                help="List of hosts to connect (in host:port format)",
            ),
            "timeout": optconf.Option(
                default=10, type=_valid_float_min_01,
                help="The longest to wait for a Zookeeper connection",
            ),
            "start-timeout": optconf.Option(
                default=10, type=_valid_float_min_01,
                help="Timeout of the initial connection",
            ),
            "start-retries": optconf.Option(
                default=None, type=_valid_float_min_1_or_none,
                help="The number of attempts the initial connection to ZooKeeper (None - infinite)",
            ),
            "randomize-hosts": optconf.Option(
                default=True, type=valid_bool,
                help="Randomize host selection",
            ),
            "chroot": optconf.Option(
                default=None, type=_valid_str_or_none,
                help="Use specified node as root (it must be created manually)",
            ),
        }

    # ===

    @contextlib.contextmanager
    def connected(self):
        self.open()
        try:
            yield self
        finally:
            self.close()

    def open(self):
        self._client.open()
        ifaces.init(self._client)

    def close(self):
        self._client.close()

    # ===

    def get_info(self):
        return self._client.get_server_info()
