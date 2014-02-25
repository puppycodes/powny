from raava import rules
from raava import comparators


##### Private classes #####
class _Cmp:
    pass
for (name, comparator) in comparators.COMPARATORS_MAP.items():
    setattr(_Cmp, name, comparator)


##### Public constants #####
BUILTINS_MAP = {
    "cmp":             _Cmp,
    "match_event":     rules.match_event,
    "match_extra":     rules.match_extra,
    "disable_handler": rules.disable_handler,
}

