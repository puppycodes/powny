import sys
import os
import yaml
import argparse
import logging
import logging.config

from ulib import typetools
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.network
import ulib.validators.python
import ulib.validators.fs

import elog.records

from . import const


##### Public constants #####
S_CORE      = "core"
S_LOGGING   = "logging"
S_SPLITTER  = "splitter"
S_WORKER    = "worker"
S_COLLECTOR = "collector"
S_API       = "api"
S_CHERRY    = "cherry"

O_ZOO_NODES     = "zoo-nodes"
O_ZOO_TIMEOUT   = "zoo-timeout"
O_ZOO_RANDOMIZE = "zoo-randomize"
O_ZOO_CHROOT    = "zoo-chroot"
O_RULES_DIR     = "rules-dir"
O_RULES_HEAD    = "rules-head"
O_IMPORT_ALIAS  = "import-alias"
O_FETCHER       = "fetcher"

O_VERSION = "version"

O_WORKERS   = "workers"
O_DIE_AFTER = "die-after"
O_QUIT_WAIT = "quit-wait"
O_RECHECK   = "recheck"

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
        O_ZOO_NODES:     (("localhost",),  validators.common.valid_string_list),
        O_ZOO_TIMEOUT:   (10,              lambda arg: validators.common.valid_number(arg, 0.1, value_type=float)),
        O_ZOO_RANDOMIZE: (True,            validators.common.valid_bool),
        O_ZOO_CHROOT:    ("/gns",          str),

        O_RULES_DIR:    (const.RULES_DIR, lambda arg: os.path.normpath(validators.fs.valid_accessible_path(arg + "/."))),
        O_RULES_HEAD:   ("HEAD",          str),
        O_IMPORT_ALIAS: (None,            _valid_maybe_empty_object),
        O_FETCHER:      (None,            _valid_maybe_empty_object),
    },

    S_LOGGING: {
        O_VERSION: (1, validators.common.valid_number),
    },

    S_SPLITTER: dict(_DAEMON_MAP),

    S_WORKER: dict(_DAEMON_MAP),

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
def init(**kwargs):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-c", "--config-dir", dest="config_dir_path", default=kwargs.pop("config_dir_path", const.CONFIG_DIR), metavar="<dir>")
    (options, argv) = parser.parse_known_args()

    options.config_dir_path = os.path.normpath(validators.fs.valid_accessible_path(options.config_dir_path + "/."))
    config = _load_config(options.config_dir_path)
    _init_logging(config)

    kwargs.update({
            "formatter_class": argparse.RawDescriptionHelpFormatter,
            "parents"        : [parser],
        })
    return (config, argparse.ArgumentParser(**kwargs), argv)


##### Private methods #####
def _init_logging(config):
    logging.setLogRecordFactory(elog.records.LogRecord) # This factory can keep the TID
    logging.captureWarnings(True)
    logging.config.dictConfig(config[S_LOGGING])


###
def _load_config(config_dir_path):
    config = make_default_config(CONFIG_MAP)
    for name in sorted(os.listdir(config_dir_path)) :
        if not name.endswith(".conf"):
            continue
        config_file_path = os.path.join(config_dir_path, name)
        with open(config_file_path) as config_file:
            try:
                typetools.merge_dicts(config, yaml.load(config_file.read()))
            except Exception:
                print("Incorrect config: %s\n-----" % (config_file_path), file=sys.stderr)
                raise
    validate_config(config, CONFIG_MAP)
    return config

def make_default_config(pattern):
    defaults = {}
    for (key, pair) in pattern.items():
        if isinstance(pair, dict):
            defaults[key] = make_default_config(pair)
        elif isinstance(pair, tuple):
            defaults[key] = pair[0]
        else:
            raise RuntimeError("Invalid CONFIG_MAP")
    return defaults

def validate_config(config, pattern, keys = ()):
    for (key, pair) in pattern.items():
        if isinstance(pair, dict):
            keys_path = list(keys) + [key]
            if not isinstance(config[key], dict):
                raise RuntimeError("The section \"%s\" must be a dict" % (".".join(keys_path)))
            validate_config(config[key], pattern[key], keys_path)
        else: # tuple
            config[key] = pair[1](config[key])

