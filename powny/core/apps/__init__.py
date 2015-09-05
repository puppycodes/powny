import sys
import argparse
import pkgutil
import threading
import socket
import logging
import logging.config
import time
import abc

import yaml

import pygments.lexers.data
import pygments.formatters

from contextlog import (
    get_logger,
    patch_logging,
    patch_threading,
)

from .. import (
    tools,
    backends,
    backdoor,
)

from ..optconf import (
    build_raw_from_options,
    make_config,
    Option,
)

from ..optconf.dumper import make_config_dump
from ..optconf.loader import load_file as load_yaml_file

from ..optconf.converters import (
    as_string_or_none,
    as_int_or_none,
)


# =====
_config = None


def get_config():
    return _config


def init(name, description, args=None, raw_config=None):
    global _config
    assert _config is None, "init() has already been called"

    args_parser = argparse.ArgumentParser(prog=name, description=description)
    args_parser.add_argument("-v", "--version", action="version", version=tools.get_version())
    args_parser.add_argument("-c", "--config", dest="config_file_path", default=None, metavar="<file>")
    args_parser.add_argument("-l", "--level", dest="log_level", default=None)
    args_parser.add_argument("-m", "--dump-config", dest="dump_config", action="store_true")
    args_parser.add_argument("-o", "--set-options", dest="set_options", default=[], nargs="+")
    options = args_parser.parse_args(args)

    # Load configs
    raw_config = (raw_config or {})
    if options.config_file_path is not None:
        raw_config = load_yaml_file(options.config_file_path)
    _merge_dicts(raw_config, build_raw_from_options(options.set_options))
    scheme = _get_config_scheme()
    config = make_config(raw_config, scheme)

    # Configure logging
    patch_logging()
    patch_threading()
    logging.setLogRecordFactory(_ClusterLogRecord)
    logging.captureWarnings(True)
    logging_config = raw_config.get("logging")
    if logging_config is None:
        logging_config = yaml.load(pkgutil.get_data(__name__, "configs/logging.yaml"))
    if options.log_level is not None:
        logging_config.setdefault("root", {})
        logging_config["root"]["level"] = _valid_log_level(options.log_level)
    logging.config.dictConfig(logging_config)

    # Update scheme for backend opts
    backend_scheme = backends.get_backend_class(config.core.backend).get_options()
    _merge_dicts(scheme, {"backend": backend_scheme})
    config = make_config(raw_config, scheme)

    # Provide global configuration
    _config = make_config(raw_config, scheme)

    # Print config dump and exit
    if options.dump_config:
        dump = make_config_dump(config)
        if sys.stdout.isatty():
            dump = pygments.highlight(
                dump,
                pygments.lexers.data.YamlLexer(),
                pygments.formatters.TerminalFormatter(bg="dark"),
            )
        print(dump)
        sys.exit(0)

    return _config


_fqdn_cached = 0


class _ClusterLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # XXX: No locks!
        # http://bugs.python.org/issue6721
        global _fqdn_cached
        stamp = int(time.time() // 60)
        if _fqdn_cached != stamp:
            self.fqdn = socket.getfqdn()
            _fqdn_cached = stamp
        self.node = tools.get_node_name()  # Nodename from uname


class Application(metaclass=abc.ABCMeta):
    def __init__(self, app_name, config):
        self._app_name = app_name
        self._app_config = config[app_name]
        self._config = config
        self._stop_event = threading.Event()
        self._respawns = 0
        self._next_write_state_at = 0

    def stop(self):
        self._stop_event.set()

    def dump_app_state(self, backend, app_state):
        if self._next_write_state_at <= time.time():
            app_state = app_state.copy()
            app_state["respawns"] = self._respawns
            backend.system_apps_state.set_state(self._app_name, app_state)
            self._next_write_state_at = time.time() + self._app_config.state_every

    def get_backend_object(self):
        return backends.get_backend_class(self._config.core.backend)(**self._config.backend)

    ###

    def run(self):
        logger = get_logger(app=self._app_name)  # App-level context
        if self._config.backdoor.enabled:
            backdoor.start(self._config.backdoor.port)
        self._respawns = 0
        while not self._stop_event.is_set():
            if self._app_config.max_fails is not None and self._respawns >= self._app_config.max_fails + 1:
                logger.critical("Reached the respawn maximum, exiting...")
                return -1
            try:
                logger.critical("Ready to work")
                self.process()
            except KeyboardInterrupt:
                logger.critical("Received Ctrl+C, exiting...")
                return 0
            except Exception:
                logger.critical("Error in main loop, respawn...", exc_info=True)
                logger.warning("Sleeping %f seconds...", self._app_config.fail_sleep)
                time.sleep(self._app_config.fail_sleep)
                self._respawns += 1
        return 0

    @abc.abstractmethod
    def process(self):
        raise NotImplementedError


# =====
def _valid_log_level(arg):
    try:
        return int(arg)
    except ValueError:
        return logging._nameToLevel[arg.upper()]  # pylint: disable=protected-access


def _merge_dicts(dest, src, path=None):
    if path is None:
        path = []
    for key in src:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(src[key], dict):
                _merge_dicts(dest[key], src[key], list(path) + [str(key)])
                continue
        dest[key] = src[key]


def _get_config_scheme():
    scheme = {
        "core": {
            "node_name": Option(default=None, type=as_string_or_none, help="Short node name (like uname -n)"),
            "backend": Option(default="zookeeper", help="Backend plugin"),
            "scripts_dir": Option(default="scripts", help="Path to scripts root"),
        },

        "backdoor": {
            "enabled": Option(default=False, help="Enable telnet-based backdoor to Python process"),
            "port": Option(default=2200, help="Backdoor port"),
        },

        "api": {
            "backend_connections": Option(default=1, help="Maximum number of backend connections"),
            "delete_timeout": Option(default=15, help="Timeout for stop/delete operation"),
            "gunicorn": Option(default={}, help="Gunicorn options (workers, max_requests, etc.) "
                                                "exclude entrypoint-specific (like errorlog, accesslog). "
                                                "See http://docs.gunicorn.org/en/latest/settings.html"),
        },

        "worker": {
            "max_jobs_sleep": Option(default=1, help="If we have reached the maximum concurrent jobs - "
                                                     "the process goes to sleep (seconds)"),
            "max_jobs": Option(default=None, type=as_int_or_none, help="The maximum number of job processes"),
            "job_delay": Option(default=0.1, help="Sleep between start of jobs"),
            "wait_slowpokes": Option(default=30.0, help="Wait slow jobs before kill"),
        },

        "collector": {},
    }
    for app in ("worker", "collector"):
        scheme[app].update({
            "max_fails": Option(default=None, type=as_int_or_none, help="Number of failures after which "
                                                                        "the program terminates"),
            "fail_sleep": Option(default=5, help="If processing fails, sleep for awhile and restart (seconds)"),
            "empty_sleep": Option(default=1, help="Interval after which process will sleep when "
                                                  "there are no jobs (seconds)"),
            "state_every": Option(default=5, help="Dump appstate to backend every this time (seconds)"),
        })
    return scheme
