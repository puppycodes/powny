from ulib import validators
import ulib.validators.common  # pylint: disable=W0611

from ...core import optconf

from . import zoo
from . import scheme


# =====
def _valid_float_min_01(arg):
    return validators.common.valid_number(arg, 0.1, value_type=float)

def _valid_number_min_1(arg):
    return validators.common.valid_number(arg, 1)

def _valid_float_min_1_or_none(arg):
    return validators.common.valid_maybe_empty(arg, _valid_number_min_1)

def _valid_str_or_none(arg):
    return validators.common.valid_maybe_empty(arg, str)


class _Stub():  # pylint: disable=W0232
    pass


class Backend:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._client = zoo.Client(**kwargs)
        self.jobs = _Stub()
        self.jobs.control = scheme.JobsControlScheme(self._client)
        self.jobs.process = scheme.JobsProcessScheme(self._client)
        self.jobs.gc = scheme.JobsGcScheme(self._client)
        self.rules = scheme.RulesScheme(self._client)
        self.system = _Stub()
        self.system.apps_state = scheme.AppsStateScheme(self._client)

    @classmethod
    def get_options(cls):
        return {
            "nodes": optconf.Option(
                default=["localhost"], validator=validators.common.valid_string_list,
                help="List of hosts to connect (in host:port format)",
            ),
            "timeout": optconf.Option(
                default=10, validator=_valid_float_min_01,
                help="The longest to wait for a Zookeeper connection",
            ),
            "start-timeout": optconf.Option(
                default=10, validator=_valid_float_min_01,
                help="Timeout of the initial connection",
            ),
            "start-retries": optconf.Option(
                default=None, validator=_valid_float_min_1_or_none,
                help="The number of attempts the initial connection to ZooKeeper (None - infinite)",
            ),
            "randomize-hosts": optconf.Option(
                default=True, validator=validators.common.valid_bool,
                help="Randomize host selection",
            ),
            "chroot": optconf.Option(
                default=None, validator=_valid_str_or_none,
                help="Use specified node as root (it must be created manually)",
            ),
        }

    def get_info(self):
        return self._client.get_server_info()

    def open(self):
        self._ensure_chroot()
        self._client.open()
        return scheme.init(self._client)

    def close(self):
        self._client.close()

    def _ensure_chroot(self):
        if self._kwargs.get("chroot") is not None:
            kwargs = dict(self._kwargs)
            kwargs["chroot"] = None
            with zoo.Client(**kwargs) as client:
                try:
                    with client.get_write_request("ensure_chroot()") as request:
                        request.create(self._kwargs["chroot"], recursive=True)
                except zoo.NodeExistsError:
                    pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
