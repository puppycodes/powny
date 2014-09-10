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

from yaml import load as load_yaml

import contextlog
from contextlog import get_logger

from ulib import typetools

from ulib.validators.common import (
    valid_number,
    valid_bool,
    valid_empty,
    valid_maybe_empty,
    valid_string_list,
)
from ulib.validators.network import (
    valid_ip_or_host,
    valid_port,
)
from ulib.validators.fs import valid_accessible_path
from ulib.validators.python import valid_object_name

from .. import tools
from .. import backends

from .. import optconf
from ..optconf.loaders.yaml import load_file as load_yaml_file


# =====
_config = None

def get_config(check_helpers=()):
    if len(check_helpers) > 0:
        for helper in check_helpers:
            if helper not in _config.helpers.configure:
                raise RuntimeError("Helper '{}' is not configured".format(helper))
    return _config


def init(name, description, args=None):
    global _config
    assert _config is None, "init() has already been called"

    args_parser = argparse.ArgumentParser(prog=name, description=description)
    args_parser.add_argument("-v", "--version", action="version", version=tools.get_powny_version())
    args_parser.add_argument("-c", "--config", dest="config_file_path", default=None, metavar="<file>")
    args_parser.add_argument("-l", "--level", dest="log_level", default=None)
    args_parser.add_argument("-m", "--dump-config", dest="dump_config", action="store_true")
    options = args_parser.parse_args(args)

    # Load configs
    raw = {}
    if options.config_file_path is not None:
        raw = load_yaml_file(options.config_file_path)
    scheme = _get_config_scheme()
    config = optconf.make_config(raw, scheme)

    # Configure logging
    contextlog.patch_logging()
    contextlog.patch_threading()
    logging.captureWarnings(True)
    logging_config = raw.get("logging")
    if logging_config is None:
        logging_config = load_yaml(pkgutil.get_data(__name__, "configs/logging.yaml"))
    if options.log_level is not None:
        logging_config.setdefault("root", {})
        logging_config["root"]["level"] = _valid_log_level(options.log_level)
    logging.config.dictConfig(logging_config)

    # Update scheme for backend opts
    backend_scheme = backends.get_backend_class(config.core.backend).get_options()
    typetools.merge_dicts(scheme, {"backend": backend_scheme})
    config = optconf.make_config(raw, scheme)

    # Update scheme for selected helpers/modules
    for helper_name in config.helpers.configure:
        helper = importlib.import_module(helper_name)
        get_options = getattr(helper, "get_options", None)
        if get_options is None:
            raise RuntimeError("Helper '{}' requires no configuration".format(helper_name))
        typetools.merge_dicts(scheme, {"helpers": get_options()})

    # Provide global configuration for helpers
    _config = optconf.make_config(raw, scheme)

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

    def get_backend_object(self):
        return backends.get_backend_class(self._config.core.backend)(**self._config.backend)

    ###

    def run(self):
        logger = get_logger(app=self._app_name)  # App-level context
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
                logger.warning("Sleeping %f seconds...", self._app_config.fail_sleep)
                time.sleep(self._app_config.fail_sleep)
                self._respawns += 1
        self.end()
        return 0

    @abc.abstractmethod
    def process(self):
        raise NotImplementedError

    def end(self):
        pass


# =====
def _valid_log_level(arg):
    try:
        return int(arg)
    except ValueError:
        return logging._nameToLevel[arg.upper()]  # pylint: disable=protected-access

def _valid_number_min_1(arg):
    return valid_number(arg, 1)

def _valid_empty_or_number_min_0(arg):
    return valid_maybe_empty(arg, lambda arg: valid_number(arg, 0))

def _get_config_scheme():
    scheme = {
        "core": {
            "node-name": optconf.Option(
                default=None, type=valid_empty,
                help="Node name, must be a unique (uname by default)",
            ),
            "backend": optconf.Option(
                default="zookeeper", type=valid_object_name,
                help="Backend plugin",
            ),
            "rules-module": optconf.Option(
                default="rules", type=valid_object_name,
                help="Name of the rules module/package",
            ),
            "rules-dir": optconf.Option(
                default="rules", type=valid_accessible_path,
                help="Path to rules root",
            ),
        },

        "helpers": {
            "configure": optconf.Option(
                default=[], type=valid_string_list,
                help="A list of modules that are configured",
            ),
        },

        "api": {
            "backend-connections": optconf.Option(
                default=5, type=_valid_number_min_1,
                help="The number of connections to the backend supported by pool",
            ),
            "input-limit": optconf.Option(
                default=20000, type=_valid_number_min_1,
                help="Limit of the input queue before 503 error",
            ),
            "delete-timeout": optconf.Option(
                default=15, type=_valid_number_min_1,
                help="Timeout for stop/delete operation",
            ),

            "run": {
                "host": optconf.Option(
                    default="localhost", type=(lambda arg: valid_ip_or_host(arg)[0]),
                    help="The host for the internal server",
                ),
                "port": optconf.Option(
                    default=7887, type=valid_port,
                    help="The port for the internal server",
                ),
                "use-threads": optconf.Option(
                    default=True, type=valid_bool,
                    help="Process each request in a separate thread",
                ),
                "processes": optconf.Option(
                    default=1, type=_valid_number_min_1,
                    help="If greater than 1 then handle each request in a new process up "
                         "to this maximum number of concurrent processes",
                ),
                "debug-console": optconf.Option(
                    default=True, type=valid_bool,
                    help="Open interactive console with exception context in browser",
                ),
            },
        },

        "worker": {
            "max-jobs-sleep": optconf.Option(
                default=1, type=_valid_number_min_1,
                help="If we have reached the maximum concurrent jobs - the process goes to sleep (seconds)",
            ),
            "max-jobs": optconf.Option(
                default=100, type=_valid_number_min_1,
                help="The maximum number of job processes",
            ),
        },

        "collector": {
            "done-lifetime": optconf.Option(
                default=60, type=_valid_number_min_1,
                help="Completed jobs are not deleted the specified number of seconds",
            ),
        },
    }
    for app in ("worker", "collector"):
        scheme[app].update({
            "max-fails": optconf.Option(
                default=None, type=_valid_empty_or_number_min_0,
                help="Maximum number of failures after which the program terminates",
            ),
            "fail-sleep": optconf.Option(
                default=5, type=_valid_number_min_1,
                help="If processing fails, sleep for awhile and restart (seconds)",
            ),
            "empty-sleep": optconf.Option(
                default=1, type=_valid_number_min_1,
                help="If there are no jobs ready for removal the process goes to sleep (seconds)",
            ),
        })
    return scheme
