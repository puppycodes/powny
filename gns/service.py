import os
import logging
import warnings

from ulib import optconf
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.fs

from . import const


##### Public constants #####
# Common
OPTION_LOG_LEVEL  = ("log-level",  "log_level",     "INFO",            str)
OPTION_LOG_FILE   = ("log-file",   "log_file_path", None,              validators.common.valid_empty)
OPTION_LOG_FORMAT = ("log-format", "log_format",    "%(asctime)s %(process)d %(threadName)s - %(levelname)s -- %(message)s", str)
OPTION_ZOO_NODES  = ("zoo-nodes",  "nodes_list",    ("localhost",),    validators.common.valid_string_list)
OPTION_RULES_DIR  = ("rules-dir",  "rules_dir",     const.RULES_DIR,   lambda arg: os.path.normpath(validators.fs.validAccessiblePath(arg + "/.")))
OPTION_RULES_HEAD = ("rules-head", "rules-head",    "HEAD",            str)
OPTION_WORKERS    = ("workers",    "workers",       10,                lambda arg: validators.common.valid_number(arg, 1))
OPTION_DIE_AFTER  = ("die-after",  "die_after",     100,               lambda arg: validators.common.valid_number(arg, 1))
OPTION_QUIT_WAIT  = ("quit-wait",  "quit_wait",     10,                lambda arg: validators.common.valid_number(arg, 0))
OPTION_INTERVAL   = ("interval",   "interval",      0.01,              lambda arg: validators.common.valid_number(arg, 0, value_type=float))
# Splitter/Worker
OPTION_QUEUE_TIMEOUT = ("queue-timeout", "queue_timeout", 1, lambda arg: validators.common.valid_number(arg, 0, value_type=float))
# Collector
OPTION_POLL_INTERVAL     = ("poll-interval",     "poll_interval",     10, lambda arg: validators.common.valid_number(arg, 1))
OPTION_ACQUIRE_DELAY     = ("acquire-delay",     "acquire_delay",     5,  lambda arg: validators.common.valid_number(arg, 1))
OPTION_RECYCLED_PRIORITY = ("recycled-priority", "recycled_priority", 0,  lambda arg: validators.common.valid_number(arg, 0))
OPTION_GARBAGE_LIFETIME  = ("garbage-lifetime",  "garbage_lifetime",  0,  lambda arg: validators.common.valid_number(arg, 0))

ALL_OPTIONS = [ value for (key, value) in globals().items() if key.startswith("OPTION_") ]

ARG_LOG_FILE   = (("-l", OPTION_LOG_FILE[0],),   OPTION_LOG_FILE,   { "action" : "store", "metavar" : "<file>" })
ARG_LOG_LEVEL  = (("-L", OPTION_LOG_LEVEL[0],),  OPTION_LOG_LEVEL,  { "action" : "store", "metavar" : "<level>" })
ARG_LOG_FORMAT = (("-F", OPTION_LOG_FORMAT[0],), OPTION_LOG_FORMAT, { "action" : "store", "metavar" : "<format>" })
ARG_ZOO_NODES  = (("-z", OPTION_ZOO_NODES[0],),  OPTION_ZOO_NODES,  { "nargs"  : "+",     "metavar" : "<hosts>" })
ARG_RULES_DIR  = (("-r", OPTION_RULES_DIR[0],),  OPTION_RULES_DIR,  { "action" : "store", "metavar" : "<dir>" })
ARG_RULES_HEAD = (("-R", OPTION_RULES_HEAD[0],), OPTION_RULES_HEAD, { "action" : "store", "metavar" : "<name>" })
ARG_WORKERS    = (("-w", OPTION_WORKERS[0],),    OPTION_WORKERS,    { "action" : "store", "metavar" : "<number>" })
ARG_DIE_AFTER  = (("-d", OPTION_DIE_AFTER[0],),  OPTION_DIE_AFTER,  { "action" : "store", "metavar" : "<seconds>" })
ARG_QUIT_WAIT  = (("-q", OPTION_QUIT_WAIT[0],),  OPTION_QUIT_WAIT,  { "action" : "store", "metavar" : "<seconds>" })
ARG_INTERVAL   = (("-i", OPTION_INTERVAL[0],),   OPTION_INTERVAL,   { "action" : "store", "metavar" : "<seconds>" })
# Splitter/Worker
ARG_QUEUE_TIMEOUT = ((OPTION_QUEUE_TIMEOUT[0],), OPTION_QUEUE_TIMEOUT, { "action" : "store", "metavar" : "<seconds>" })

# Collector
ARG_POLL_INTERVAL     = ((OPTION_POLL_INTERVAL[0],),     OPTION_POLL_INTERVAL,     { "action" : "store", "metavar" : "<seconds>" })
ARG_ACQUIRE_DELAY     = ((OPTION_ACQUIRE_DELAY[0],),     OPTION_ACQUIRE_DELAY,     { "action" : "store", "metavar" : "<seconds>" })
ARG_RECYCLED_PRIORITY = ((OPTION_RECYCLED_PRIORITY[0],), OPTION_RECYCLED_PRIORITY, { "action" : "store", "metavar" : "<number>" })
ARG_GARBAGE_LIFETIME  = ((OPTION_GARBAGE_LIFETIME[0],),  OPTION_GARBAGE_LIFETIME,  { "action" : "store", "metavar" : "<seconds>" })


##### Public methods #####
def parse_options(app_section, args_list, config_file_path=const.CONFIG_FILE):
    parser = optconf.OptionsConfig(ALL_OPTIONS, config_file_path)
    for arg_tuple in (
            ARG_LOG_FILE,
            ARG_LOG_LEVEL,
            ARG_LOG_FORMAT,
            ARG_ZOO_NODES,
            ARG_WORKERS,
            ARG_DIE_AFTER,
            ARG_QUIT_WAIT,
            ARG_INTERVAL,
        ) + tuple(args_list) :
        parser.add_argument(arg_tuple)
    options = parser.sync(("main", app_section))[0]
    return options

def init_logging(options):
    level = options[OPTION_LOG_LEVEL]
    log_file_path = options[OPTION_LOG_FILE]
    line_format = options[OPTION_LOG_FORMAT]

    root = logging.getLogger()
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

