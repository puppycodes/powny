import sys
import os
import yaml
import argparse
import logging
import warnings

from ulib import typetools
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.network
import ulib.validators.fs

from . import const


##### Public constants #####
S_CORE      = "core"
S_LOGGING   = "logging"
S_SPLITTER  = "splitter"
S_WORKER    = "worker"
S_COLLECTOR = "collector"
S_API       = "api"

O_ZOO_NODES  = "zoo-nodes"
O_RULES_DIR  = "rules-dir"
O_RULES_HEAD = "rules-head"

O_LOG_LEVEL  = "log-level"
O_LOG_FILE   = "log-file"
O_LOG_FORMAT = "log-format"

O_WORKERS   = "workers"
O_DIE_AFTER = "die-after"
O_QUIT_WAIT = "quit-wait"
O_RECHECK   = "recheck"

O_QUEUE_TIMEOUT     = "queue-timeout"
O_ACQUIRE_DELAY     = "acquire-delay"
O_POLL_INTERVAL     = "poll-interval"
O_RECYCLED_PRIORITY = "recycled-priority"
O_GARBAGE_LIFETIME  = "garbage-lifetime"
O_HOST              = "host"
O_PORT              = "port"


###
class _Option:
    def __init__(self, default, validator):
        self._default = default
        self._validator = validator

    def get_default(self):
        return self._default

    def get_validator(self):
        return self._validator

_DAEMON_MAP = {
    O_WORKERS:   (10,   lambda arg: validators.common.valid_number(arg, 1)),
    O_DIE_AFTER: (100,  lambda arg: validators.common.valid_number(arg, 1)),
    O_QUIT_WAIT: (10,   lambda arg: validators.common.valid_number(arg, 0)),
    O_RECHECK:   (0.01, lambda arg: validators.common.valid_number(arg, 0, value_type=float)),
}

CONFIG_MAP = {
    S_CORE: {
        O_ZOO_NODES:  (("localhost",),  validators.common.valid_string_list),
        O_RULES_DIR:  (const.RULES_DIR, lambda arg: os.path.normpath(validators.fs.validAccessiblePath(arg + "/."))),
        O_RULES_HEAD: ("HEAD",          str),
    },

    S_LOGGING: {
        O_LOG_LEVEL:  ("INFO", str),
        O_LOG_FILE:   (None,   validators.common.valid_empty),
        O_LOG_FORMAT: ("%(asctime)s %(process)d %(threadName)s - %(levelname)s -- %(message)s", str),
    },

    S_SPLITTER: typetools.merge_dicts({
            O_QUEUE_TIMEOUT: (1, lambda arg: validators.common.valid_number(arg, 0, value_type=float)),
        }, dict(_DAEMON_MAP)),

    S_WORKER: typetools.merge_dicts({
            O_QUEUE_TIMEOUT: (1, lambda arg: validators.common.valid_number(arg, 0, value_type=float)),
        }, dict(_DAEMON_MAP)),

    S_COLLECTOR: typetools.merge_dicts({
            O_POLL_INTERVAL:     (10, lambda arg: validators.common.valid_number(arg, 1)),
            O_ACQUIRE_DELAY:     (5,  lambda arg: validators.common.valid_number(arg, 1)),
            O_RECYCLED_PRIORITY: (0,  lambda arg: validators.common.valid_number(arg, 0)),
            O_GARBAGE_LIFETIME:  (0,  lambda arg: validators.common.valid_number(arg, 0)),
        }, dict(_DAEMON_MAP)),

    S_API: {
            O_HOST: ("0.0.0.0", lambda arg: validators.network.valid_ip_or_host(arg)[0]),
            O_PORT: (7887,      validators.network.valid_port),
        },
}


##### Public methods #####
def init(**kwargs_dict):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-c", "--config-dir", dest="config_dir_path", default=const.CONFIG_DIR, metavar="<dir>",
        type=( lambda arg: os.path.normpath(validators.fs.validAccessiblePath(arg + "/.")) ))
    (options, remaining_list) = parser.parse_known_args()

    config_dict = _load_config(options.config_dir_path)
    _init_logging(config_dict)

    kwargs_dict.update({
            "formatter_class" : argparse.RawDescriptionHelpFormatter,
            "parents"         : [parser],
        })
    return (config_dict, argparse.ArgumentParser(**kwargs_dict), remaining_list)


##### Private methods #####
def _init_logging(config_dict):
    level = config_dict[S_LOGGING][O_LOG_LEVEL]
    log_file_path = config_dict[S_LOGGING][O_LOG_FILE]
    line_format = config_dict[S_LOGGING][O_LOG_FORMAT]

    root = logging.getLogger("raava")
    root.setLevel(level)
    if line_format is None:
        line_format = "%(asctime)s %(process)d %(threadName)s - %(levelname)s -- %(message)s"
    formatter = logging.Formatter(line_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    if log_file_path is not None:
        file_handler = logging.handlers.WatchedFileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    def log_warning(message, category, filename, lineno, file=None, line=None) : # pylint: disable=W0622
        root.warning("Python warning: %s", warnings.formatwarning(message, category, filename, lineno, line))

    warnings.showwarning = log_warning


###
def _load_config(config_dir_path):
    config_dict = _make_default_config()
    for name in sorted(os.listdir(config_dir_path)) :
        if not name.endswith(".conf"):
            continue
        config_file_path = os.path.join(config_dir_path, name)
        with open(config_file_path) as config_file:
            try:
                typetools.merge_dicts(config_dict, yaml.load(config_file.read()))
            except Exception:
                print("Incorrect config: %s\n-----" % (config_file_path), file=sys.stderr)
                raise
    _validate_config(config_dict)
    return config_dict

def _make_default_config(start_dict = CONFIG_MAP):
    default_dict = {}
    for (key, value) in start_dict.items():
        if isinstance(value, dict):
            default_dict[key] = _make_default_config(value)
        elif isinstance(value, tuple):
            default_dict[key] = value[0]
        else:
            raise RuntimeError("Invalid CONFIG_MAP")
    return default_dict

def _validate_config(config_dict, std_dict = CONFIG_MAP, keys_list = []):
    for (key, pair) in std_dict.items():
        if isinstance(pair, dict):
            current_list = keys_list + [key]
            if not isinstance(config_dict[key], dict):
                raise RuntimeError("The section \"%s\" must be a dict" % (".".join(current_list)))
            _validate_config(config_dict[key], std_dict[key], current_list)
        else: # tuple
            config_dict[key] = pair[1](config_dict[key])

