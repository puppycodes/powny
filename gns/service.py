import sys
import os
import yaml
import yaml.loader
import argparse
import logging
import logging.config

from ulib import typetools
from ulib import validatorlib
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.network
import ulib.validators.python
import ulib.validators.fs

import elog.records
import meters

from . import const


##### Public constants #####
S_CORE      = "core"
S_LOGGING   = "logging"
S_METERS    = "meters"
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

        O_RULES_DIR:    (const.RULES_DIR, str),
        O_RULES_HEAD:   ("HEAD",          str),
        O_IMPORT_ALIAS: (None,            _valid_maybe_empty_object),
        O_FETCHER:      (None,            _valid_maybe_empty_object),
    },

    S_LOGGING: {
        O_VERSION: (1, validators.common.valid_number),
    },

    S_METERS: {},

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


##### Exceptions #####
class ConfigError(Exception):
    pass


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public methods #####
def init(**kwargs):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-c", "--config", dest="config_file_path", default=None, metavar="<file>")
    (options, argv) = parser.parse_known_args()

    try:
        config_file_path = options.config_file_path
        if config_file_path is not None:
            # Validate --config
            config_file_path = os.path.normpath(validators.fs.valid_accessible_path(config_file_path))
        else:
            config_file_path = kwargs.pop("config_file_path", const.CONFIG_FILE)
            if not os.access(config_file_path, os.F_OK):
                config_file_path = None # Default config file is not a necessary
        config = load_config(config_file_path)
    except (ConfigError, validatorlib.ValidatorError) as err:
        _logger.error("Incorrect configuration: %s", err) # Fallback logging
        sys.exit(1)

    _init_logging(config)
    _init_meters(config)

    kwargs.update({
            "formatter_class": argparse.RawDescriptionHelpFormatter,
            "parents"        : [parser],
        })
    return (config, argparse.ArgumentParser(**kwargs), argv)


###
def load_config(config_file_path):
    _logger.debug("Making a default confing...")
    config = make_default_config(CONFIG_MAP)
    if config_file_path is not None:
        with open(config_file_path) as config_file:
            typetools.merge_dicts(config, _load_yaml(config_file))
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
            raise RuntimeError("Programming error: invalid CONFIG_MAP")
    return defaults

def validate_config(config, pattern, keys = ()):
    for (key, pair) in pattern.items():
        keys_path = tuple(keys) + (key,)
        option_name = ".".join(keys_path)
        if isinstance(pair, dict):
            if not isinstance(config[key], dict):
                raise ConfigError("The section \"%s\" must be a dict" % (option_name))
            validate_config(config[key], pattern[key], keys_path)
        else: # tuple
            try:
                config[key] = pair[1](config[key])
            except validatorlib.ValidatorError as err:
                raise ConfigError("Invalid value for \"%s\": %s" % (option_name, err))


##### Private methods #####
def _init_logging(config):
    logging.setLogRecordFactory(elog.records.LogRecord) # This factory can keep the TID
    logging.captureWarnings(True)
    logging.config.dictConfig(config[S_LOGGING])

def _init_meters(config):
    meters.configure(config[S_METERS])
    meters.start()

def _load_yaml(stream):
    _logger.debug("Loading config from \"%s\"...", stream.name)
    try:
        return yaml.load(stream, _YamlLoader)
    except Exception as err:
        raise ConfigError("Incorrect YAML syntax in \"%s\":\n%s" % (stream.name, err))


##### Private classes #####
class _YamlLoader(yaml.loader.Loader):
    def __init__(self, stream):
        yaml.loader.Loader.__init__(self, stream)
        self._root = os.path.dirname(stream.name)

    def include(self, node):
        file_path = os.path.join(self._root, self.construct_scalar(node)) # pylint: disable=E1101
        _logger.debug("Including config \"%s\"...", file_path)
        with open(file_path) as stream:
            return _load_yaml(stream)
_YamlLoader.add_constructor("!include", _YamlLoader.include) # pylint: disable=E1101

