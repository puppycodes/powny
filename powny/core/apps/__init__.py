import sys
import argparse
import importlib
import pkgutil
import threading
import logging
import logging.config
import platform
import socket
import time
import abc

from contextlog import get_logger

import yaml

from ulib import ui
import ulib.ui.term  # pylint: disable=W0611

from ulib import validators
import ulib.validators.common  # pylint: disable=W0611
import ulib.validators.python
import ulib.validators.network
import ulib.validators.fs

from .. import tools
from .. import backends
from .. import optconf


# =====
_config = None

def get_config(check_helpers=()):
    if len(check_helpers) > 0:
        for helper in check_helpers:
            if helper not in _config.helpers.configure:
                raise RuntimeError("Helper '{}' is not configured".format(helper))
    return _config


def init(name, description, args=None):
    global _config  # pylint: disable=W0603
    assert _config is None, "init() has already been called"

    args_parser = argparse.ArgumentParser(prog=name, description=description)
    args_parser.add_argument("-v", "--version", action="version", version=tools.get_powny_version())
    args_parser.add_argument("-c", "--config", dest="config_file_path", default=None, metavar="<file>")
    args_parser.add_argument("-l", "--level", dest="log_level", default=None)
    args_parser.add_argument("-m", "--dump-config", dest="dump_config", action="store_true")
    options = args_parser.parse_args(args)

    # Load configs
    conf_parser = optconf.YamlLoader(_get_config_scheme(), options.config_file_path)
    conf_parser.load()

    # Configure logging
    logging.captureWarnings(True)
    logging_config = conf_parser.get_raw().get("logging")
    if logging_config is None:
        logging_config = yaml.load(pkgutil.get_data(__name__, "config/logging.yaml"))
    if options.log_level is not None:
        logging_config.setdefault("root", {})
        logging_config["root"]["level"] = options.log_level
    logging.config.dictConfig(logging_config)

    # Load backend opts
    backend_name = conf_parser.get_config().core.backend
    backend_scheme = backends.get_backend(backend_name).get_options()
    conf_parser.update_scheme({"backend": backend_scheme})

    # Configure selected helpers/modules
    for helper_name in conf_parser.get_config().helpers.configure:
        helper = importlib.import_module(helper_name)
        get_options = getattr(helper, "get_options", None)
        if get_options is None:
            raise RuntimeError("Helper '{}' requires no configuration".format(helper_name))
        conf_parser.update_scheme({"helpers": get_options()})

    # Provide global configuration for helpers
    _config = conf_parser.get_config()

    # Print config dump and exit
    if options.dump_config:
        optconf.print_config_dump(_config, ((), ("helpers",)))
        sys.exit(0)

    return _config


class Application(metaclass=abc.ABCMeta):
    def __init__(self, app_name, config):
        self._app_name = app_name
        self._app_config = config[app_name]
        self._config = config
        self._stop_event = threading.Event()
        self._respawns = 0

    def make_write_app_state(self, app_state):
        node_name = (self._config.core.node_name or platform.uname()[1])
        state = {
            "when": time.time(),
            "host": {
                "node": node_name,
                "fqdn": socket.getfqdn(),
            },
            "state": {
                "respawns": self._respawns,
            },
        }
        state["state"].update(app_state)
        return (node_name, self._app_name, state)

    def stop(self):
        self._stop_event.set()

    def run(self):
        logger = get_logger()
        self._respawns = 0
        while not self._stop_event.is_set():
            if self._app_config.max_fails is not None and self._respawns >= self._app_config.max_fails + 1:
                logger.error("Reached the respawn maximum, exiting...")
                return -1
            try:
                self.process()
            except KeyboardInterrupt:
                logger.info("Received Ctrl+C, exiting...")
                return 0
            except Exception:
                logger.exception("Error in main loop, respawn...")
                self.respawn()
                logger.warning("Sleeping %f seconds...", self._app_config.fail_sleep)
                time.sleep(self._app_config.fail_sleep)
                self._respawns += 1
        self.cleanup()
        return 0

    @abc.abstractmethod
    def process(self):
        raise NotImplementedError

    def respawn(self):
        pass

    def cleanup(self):
        pass


# =====
def _valid_number_min_1(arg):
    return validators.common.valid_number(arg, 1)

def _valid_empty_or_number_min_0(arg):
    return validators.common.valid_maybe_empty(arg, lambda arg: validators.common.valid_number(arg, 0))

def _get_config_scheme():
    return {
        "core": {
            "node-name": optconf.Option(
                default=None, validator=validators.common.valid_empty,
                help="Node name, must be a unique (uname by default)",
            ),
            "backend": optconf.Option(
                default="zookeeper", validator=validators.python.valid_object_name,
                help="Backend plugin",
            ),
            "rules-module": optconf.Option(
                default="rules", validator=validators.python.valid_object_name,
                help="Name of the rules module/package",
            ),
            "rules-dir": optconf.Option(
                default="rules", validator=validators.fs.valid_accessible_path,
                help="Path to rules root",
            ),
        },

        "helpers": {
            "configure": optconf.Option(
                default=[], validator=validators.common.valid_string_list,
                help="A list of modules that are configured",
            ),
        },

        "api": {
            "backend-connections": optconf.Option(
                default=5, validator=_valid_number_min_1,
                help="The number of connections to the backend supported by pool",
            ),
            "input-limit": optconf.Option(
                default=20000, validator=_valid_number_min_1,
                help="Limit of the input queue before 503 error",
            ),
            "delete-timeout": optconf.Option(
                default=15, validator=_valid_number_min_1,
                help="Timeout for stop/delete operation",
            ),

            "run": {
                "host": optconf.Option(
                    default="localhost", validator=(lambda arg: validators.network.valid_ip_or_host(arg)[0]),
                    help="The host for the internal server",
                ),
                "port": optconf.Option(
                    default=7887, validator=validators.network.valid_port,
                    help="The port for the internal server",
                ),
                "use-threads": optconf.Option(
                    default=True, validator=validators.common.valid_bool,
                    help="Process each request in a separate thread",
                ),
                "processes": optconf.Option(
                    default=1, validator=_valid_number_min_1,
                    help="If greater than 1 then handle each request in a new process up "
                         "to this maximum number of concurrent processes",
                ),
                "debug-console": optconf.Option(
                    default=True, validator=validators.common.valid_bool,
                    help="Open interactive console with exception context in browser",
                ),
            },
        },

        "worker": {
            "max-fails": optconf.Option(
                default=None, validator=_valid_empty_or_number_min_0,
                help="Maximum number of failures after which the program terminates",
            ),
            "fail-sleep": optconf.Option(
                default=5, validator=_valid_number_min_1,
                help="If processing fails, sleep for awhile and restart (seconds)",
            ),
            "empty-sleep": optconf.Option(
                default=1, validator=_valid_number_min_1,
                help="If there are no jobs ready for removal - the process goes to sleep (seconds)",
            ),
            "max-jobs-sleep": optconf.Option(
                default=1, validator=_valid_number_min_1,
                help="If we have reached the maximum concurrent jobs - the process goes to sleep (seconds)",
            ),
            "max-jobs": optconf.Option(
                default=100, validator=_valid_number_min_1,
                help="The maximum number of job processes",
            ),
        },

        "collector": {
            "max-fails": optconf.Option(
                default=None, validator=_valid_empty_or_number_min_0,
                help="Maximum number of failures after which the program terminates",
            ),
            "fail-sleep": optconf.Option(
                default=5, validator=_valid_number_min_1,
                help="If processing fails, sleep for awhile and restart (seconds)",
            ),
            "empty-sleep": optconf.Option(
                default=1, validator=_valid_number_min_1,
                help="If there are no jobs ready for removal the process goes to sleep (seconds)",
            ),
            "done-lifetime": optconf.Option(
                default=60, validator=_valid_number_min_1,
                help="Completed jobs are not deleted the specified number of seconds",
            ),
        },
    }
