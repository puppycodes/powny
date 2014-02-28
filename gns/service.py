import sys
import os
import yaml
import argparse
import logging
import logging.config
import warnings

from ulib import typetools
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.network
import ulib.validators.python
import ulib.validators.fs

from . import const


##### Public constants #####
S_CORE      = "core"
S_LOGGING   = "logging"
S_SPLITTER  = "splitter"
S_WORKER    = "worker"
S_COLLECTOR = "collector"
S_API       = "api"
S_CHERRY    = "cherry"

O_ZOO_NODES    = "zoo-nodes"
O_RULES_DIR    = "rules-dir"
O_RULES_HEAD   = "rules-head"
O_IMPORT_ALIAS = "import-alias"
O_FETCHER      = "fetcher"

O_VERSION = "version"

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
def _valid_float_min_0(arg):
    return validators.common.valid_number(arg, 0, value_type=float)

def _valid_number_min_0(arg):
    return validators.common.valid_number(arg, 0)

def _valid_number_min_1(arg):
    return validators.common.valid_number(arg, 1)

def _valid_maybe_empty_object(arg):
    return validators.common.valid_maybe_empty(arg, validators.python.valid_object_name)

_DAEMON_MAP = {
    O_WORKERS:   (10,   _valid_number_min_1),
    O_DIE_AFTER: (100,  _valid_number_min_1),
    O_QUIT_WAIT: (10,   _valid_number_min_0),
    O_RECHECK:   (0.01, _valid_float_min_0),
}

CONFIG_MAP = {
    S_CORE: {
        O_ZOO_NODES:    (("localhost",),  validators.common.valid_string_list),
        O_RULES_DIR:    (const.RULES_DIR, lambda arg: os.path.normpath(validators.fs.valid_accessible_path(arg + "/."))),
        O_RULES_HEAD:   ("HEAD",          str),
        O_IMPORT_ALIAS: (None,            _valid_maybe_empty_object),
        O_FETCHER:      (None,            _valid_maybe_empty_object),
    },

    S_LOGGING: {
        O_VERSION: (1, validators.common.valid_number),
    },

    S_SPLITTER: typetools.merge_dicts({
            O_QUEUE_TIMEOUT: (1, _valid_float_min_0),
        }, dict(_DAEMON_MAP)),

    S_WORKER: typetools.merge_dicts({
            O_QUEUE_TIMEOUT: (1, _valid_float_min_0),
        }, dict(_DAEMON_MAP)),

    S_COLLECTOR: typetools.merge_dicts({
            O_POLL_INTERVAL:     (10, _valid_number_min_1),
            O_ACQUIRE_DELAY:     (5,  _valid_number_min_1),
            O_RECYCLED_PRIORITY: (0,  _valid_number_min_0),
            O_GARBAGE_LIFETIME:  (0,  _valid_number_min_0),
        }, dict(_DAEMON_MAP)),

    S_API: {},

    S_CHERRY: {
        "global": {
            "server.socket_host": ("0.0.0.0", lambda arg: validators.network.valid_ip_or_host(arg)[0]),
            "server.socket_port": (7887,      validators.network.valid_port),
        },
    },
}


##### Public methods #####
def init(**kwargs_dict):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-c", "--config-dir", dest="config_dir_path", default=kwargs_dict.pop("config_dir_path", const.CONFIG_DIR), metavar="<dir>")
    (options, remaining_list) = parser.parse_known_args()

    options.config_dir_path = os.path.normpath(validators.fs.valid_accessible_path(options.config_dir_path + "/."))
    config_dict = _load_config(options.config_dir_path)
    _init_logging(config_dict)

    kwargs_dict.update({
            "formatter_class" : argparse.RawDescriptionHelpFormatter,
            "parents"         : [parser],
        })
    return (config_dict, argparse.ArgumentParser(**kwargs_dict), remaining_list)


##### Private methods #####
def _init_logging(config_dict):
    logging.config.dictConfig(config_dict[S_LOGGING])

    def log_warning(message, category, filename, lineno, file=None, line=None) : # pylint: disable=W0622
        logging.getLogger().warning("Python warning: %s", warnings.formatwarning(message, category, filename, lineno, line))

    warnings.showwarning = log_warning


###
def _load_config(config_dir_path):
    config_dict = make_default_config(CONFIG_MAP)
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
    validate_config(config_dict, CONFIG_MAP)
    return config_dict

def make_default_config(start_dict):
    default_dict = {}
    for (key, value) in start_dict.items():
        if isinstance(value, dict):
            default_dict[key] = make_default_config(value)
        elif isinstance(value, tuple):
            default_dict[key] = value[0]
        else:
            raise RuntimeError("Invalid CONFIG_MAP")
    return default_dict

def validate_config(config_dict, std_dict, keys_list = ()):
    for (key, pair) in std_dict.items():
        if isinstance(pair, dict):
            current_list = list(keys_list) + [key]
            if not isinstance(config_dict[key], dict):
                raise RuntimeError("The section \"%s\" must be a dict" % (".".join(current_list)))
            validate_config(config_dict[key], std_dict[key], current_list)
        else: # tuple
            config_dict[key] = pair[1](config_dict[key])

