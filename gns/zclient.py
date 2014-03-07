from raava import zoo
from . import service


##### Public methods #####
def connect(config):
    core_attrs = config[service.S_CORE]
    client = zoo.connect(
        zoo_nodes=core_attrs[service.O_ZOO_NODES],
        timeout=core_attrs[service.O_ZOO_TIMEOUT],
        randomize_hosts=core_attrs[service.O_ZOO_RANDOMIZE],
    )
    return client


##### Public classes #####
class Connect:
    def __init__(self, config):
        self._config = config
        self._client = None

    def __enter__(self):
        self._client = connect(self._config)
        return self._client

    def __exit__(self, type, value, traceback): # pylint: disable=W0622
        self._client.stop()
        self._client = None

