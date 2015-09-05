import contextlib

from . import (
    zoo,
    ifaces,
)


# =====
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
        self.scripts = ifaces.Scripts(self._client)  # API and internal interface to control the scripts
        self.system_apps_state = ifaces.AppsState(self._client)  # API and internal interface to the system statistics
        self.cas_storage = ifaces.CasStorage(self._client)  # Basic CAS storage for user scripts

    @classmethod
    def get_options(cls):
        return zoo.Client.get_options()

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

    def is_opened(self):
        return self._client.is_opened()

    def is_alive(self):
        return self._client.is_alive()

    # ===

    def get_info(self):
        return self._client.get_server_info()
