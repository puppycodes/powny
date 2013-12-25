import time

from raava import worker
from raava import rules


##### Public constants #####
class EVENT:
    HOST    = "host"
    SERVICE = "service"
    LEVEL   = "level"
    INFO    = "info"

class EXTRA(rules.EXTRA):
    URGENCY = "urgency"
    USER    = "user"
    METHOD  = "method"


###
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

class METHOD:
    EMAIL = "email"
    SMS   = "sms"

class HANDLER:
    ON_EVENT  = "on_event"
    ON_NOTIFY = "on_notify"
    ON_SEND   = "on_send"


##### Stubs #####
def builtin_notify(task, event_root, user, wait = 0):
    task.checkpoint()
    event_root = event_root.copy()
    event_root.get_extra()[EXTRA.USER] = user
    task.fork(event_root, HANDLER.ON_NOTIFY)
    print("\x1b[31;1mNOTIFY: user=%s, sleep=%d\x1b[0m" % (user, wait))
    task.checkpoint()
    time.sleep(wait)
    task.checkpoint()

def builtin_send(task, event_root, method, wait = 0):
    task.checkpoint()
    event_root = event_root.copy()
    event_root.get_extra()[EXTRA.METHOD] = method
    task.fork(event_root, HANDLER.ON_SEND)
    print("\x1b[31;1mSEND: user=%s, method=%s, sleep=%d\x1b[0m" % (event_root.get_extra()[EXTRA.USER], method, wait))
    task.checkpoint()
    time.sleep(wait)
    task.checkpoint()


##### Public constants #####
MATCHER_BUILTINS_MAP = {
    "EVENT":   EVENT,
    "EXTRA":   EXTRA,
    "LEVEL":   LEVEL,
    "URGENCY": URGENCY,
    "METHOD":  METHOD,
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

    "match_event":     rules.match_event,
    "match_extra":     rules.match_extra,
    "disable_handler": rules.disable_handler,
}

WORKER_BUILTINS_MAP = {
    "notify": worker.make_task_builtin(builtin_notify),
    "send":   worker.make_task_builtin(builtin_send),
}
WORKER_BUILTINS_MAP.update(MATCHER_BUILTINS_MAP)

