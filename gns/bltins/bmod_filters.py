from raava import rules


##### Private classes #####
class _Cmp:
    eq = rules.EqComparator # XXX: eq: key=value
    ne = rules.NeComparator
    ge = rules.GeComparator
    gt = rules.GtComparator
    le = rules.LeComparator
    lt = rules.LtComparator
    in_list = rules.InListComparator
    not_in_list = rules.NotInListComparator
    regexp = rules.RegexpComparator


##### Public constants #####
BUILTINS_MAP = {
    "cmp":             _Cmp,
    "match_event":     rules.match_event,
    "match_extra":     rules.match_extra,
    "disable_handler": rules.disable_handler,
}

