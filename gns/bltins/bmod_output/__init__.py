import functools

from ulib import typetools

from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from . import email
from . import ya_sms


##### Public constants #####
S_OUTPUT = "output"
O_NOOP = "noop"


###
CONFIG_MAP = functools.reduce(typetools.merge_dicts, (
        {
            S_OUTPUT: {
                O_NOOP: (False, validators.common.valid_bool),
            }
        },
        email.CONFIG_MAP,
        ya_sms.CONFIG_MAP,
    ))

BUILTINS_MAP = functools.reduce(typetools.merge_dicts, (
        {},
        email.BUILTINS_MAP,
        ya_sms.BUILTINS_MAP,
    ))

