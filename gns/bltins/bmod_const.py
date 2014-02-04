from raava import rules
from .. import gnsint


##### Public constants #####
class EVENT:
    HOST    = "host"
    SERVICE = "service"
    STATUS  = "status"
    INFO    = "info"

class EXTRA(rules.EXTRA):
    URGENCY = "urgency"
    USER    = "user"
    METHOD  = "method"


###
class STATUS:
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

###
BUILTINS_MAP = {
    "EVENT":   EVENT,
    "EXTRA":   EXTRA,
    "STATUS":  STATUS,
    "URGENCY": URGENCY,
    "METHOD":  METHOD,
    "HANDLER": gnsint.HANDLER,
}

