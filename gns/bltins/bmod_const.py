##### _Private constants #####
class _EVENT:
    HOST    = "host"
    SERVICE = "service"
    STATUS  = "status"
    DESC    = "description"


###
class _STATUS:
    OK   = "OK"
    INFO = "INFO"
    WARN = "WARN"
    CRIT = "CRIT"

###
BUILTINS_MAP = {
    "EVENT":   _EVENT,
    "STATUS":  _STATUS,
}

