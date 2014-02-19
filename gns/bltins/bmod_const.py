##### _Private constants #####
class _EVENT:
    HOST    = "host"
    SERVICE = "service"
    STATUS  = "status"
    DESC    = "description"


###
class _STATUS:
    CRIT   = 0
    WARN   = 1
    OK     = 2
    CUSTOM = 3

###
BUILTINS_MAP = {
    "EVENT":   _EVENT,
    "STATUS":  _STATUS,
}

