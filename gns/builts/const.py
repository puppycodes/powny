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

