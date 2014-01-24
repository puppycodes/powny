from raava import worker
from raava import rules

from . import const
from . import stub


##### Public constants #####
MATCHER_BUILTINS_MAP = {
    "EVENT":   const.EVENT,
    "EXTRA":   const.EXTRA,
    "LEVEL":   const.LEVEL,
    "URGENCY": const.URGENCY,
    "METHOD":  const.METHOD,
    "HANDLER": const.HANDLER,

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
    "notify":     worker.make_task_builtin(stub.builtin_notify),
    "send":       worker.make_task_builtin(stub.builtin_send),
}
WORKER_BUILTINS_MAP.update(MATCHER_BUILTINS_MAP)

