from ulib import validators
import ulib.validators.common # pylint: disable=W0611


##### Public constants #####
LOGGER_NAME = "output"

S_OUTPUT = "output"
O_NOOP   = "noop"


###
CONFIG_MAP = {
    S_OUTPUT: {
        O_NOOP: (False, validators.common.valid_bool),
    },
}

