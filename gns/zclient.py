import contextlib

from raava import zoo
from . import service


##### Public methods #####
def connect(config):
    core_attrs = config[service.S_CORE]
    client = zoo.connect(
        zoo_nodes=core_attrs[service.O_ZOO_NODES],
        timeout=core_attrs[service.O_ZOO_TIMEOUT],
        randomize_hosts=core_attrs[service.O_ZOO_RANDOMIZE],
        chroot=core_attrs[service.O_ZOO_CHROOT],
    )
    return client

@contextlib.contextmanager
def get_context(config): # pylint: disable=C0103
    client = connect(config)
    try:
        yield client
    finally:
        zoo.close(client)

