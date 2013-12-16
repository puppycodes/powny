import time
import logging

from raava import worker
from raava import rules
from raava import const


EVENT_LEVEL = "level"
EXTRA_URGENCY = "urgency"

class LEVEL:
    CRIT   = 0
    WARN   = 1
    OK     = 2
    CUSTOM = 3

class URGENCY:
    HIGH   = 0
    MEDIUM = 1
    LOW    = 2
    CUSTOM = 3

class HANDLER:
    ON_EVENT  = "on_event"
    ON_NOTIFY = "on_notify"
    ON_SEND   = "on_send"

def _task_notify(task, *args_tuple, **kwargs_dict):
    task.checkpoint()
    print("\x1b[31;1mNOTIFY:", args_tuple, kwargs_dict, "\x1b[0m")
    time.sleep(2)
    task.checkpoint()

def _task_fork(task, event_root, handler_type):
    task.checkpoint()
    task.fork(event_root, handler_type)
    print("\x1b[31;1mFORK:", event_root, handler_type, "\x1b[0m")
    task.checkpoint()

MATCHER_BUILTINS_MAP = {
    "LEVEL":   LEVEL,
    "URGENCY": URGENCY,
    "HANDLER": HANDLER,

    "eq":          rules.EqComparator, # XXX: eq: key=value
    "ne":          rules.NeComparator,
    "ge":          rules.GeComparator,
    "gt":          rules.GtComparator,
    "le":          rules.LeComparator,
    "lt":          rules.LtComparator,
    "in_list":     rules.InListComparator,
    "not_in_list": rules.NotInListComparator,
    "regexp":      rules.RegexpComparator,

    "match_event": rules.match_event,
    "match_extra": rules.match_extra,
}

WORKER_BUILTINS_MAP = {
    "notify": worker.make_task_builtin(_task_notify),
    "fork":   worker.make_task_builtin(_task_fork),
}
WORKER_BUILTINS_MAP.update(MATCHER_BUILTINS_MAP)
