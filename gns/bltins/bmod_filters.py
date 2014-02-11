from raava import rules


##### Public constants #####
BUILTINS_MAP = {
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

