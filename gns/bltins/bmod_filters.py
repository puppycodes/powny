from raava import rules
from raava import comparators


##### Private classes #####
class _Cmp:
    eq = comparators.EqComparator # XXX: eq: key=value
    ne = comparators.NeComparator
    ge = comparators.GeComparator
    gt = comparators.GtComparator
    le = comparators.LeComparator
    lt = comparators.LtComparator
    in_list = comparators.InListComparator
    not_in_list = comparators.NotInListComparator
    regexp = comparators.RegexpComparator


##### Public constants #####
BUILTINS_MAP = {
    "cmp":             _Cmp,
    "match_event":     rules.match_event,
    "match_extra":     rules.match_extra,
    "disable_handler": rules.disable_handler,
}

