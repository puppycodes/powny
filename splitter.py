#!/usr/bin/env pypy3


from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from raava import service
from raava import rules
from raava import handlers

from raava import apps
import raava.apps.splitter # pylint: disable=W0611

import gns


##### Public constants #####
SPLITTER_SECTION = "splitter"
OPTION_QUEUE_TIMEOUT = ("queue-timeout", "queue_timeout", 1, lambda arg: validators.common.validNumber(arg, 0, value_type=float))
ARG_QUEUE_TIMEOUT = ((OPTION_QUEUE_TIMEOUT[0],), OPTION_QUEUE_TIMEOUT, { "action" : "store", "metavar" : "<seconds>" })


##### Public classes #####
class SplitterMain(service.Main):
    def construct(self, options):
        rules.setup_builtins(gns.MATCHER_BUILTINS_MAP)
        hstorage = handlers.Handlers("demo", (gns.HANDLER.ON_EVENT, gns.HANDLER.ON_NOTIFY, gns.HANDLER.ON_SEND)) # FIXME: demo path
        hstorage.load_handlers()
        return (
            getattr(options, service.OPTION_ZOO_NODES[1]), # TODO: getattr
            hstorage,
            getattr(options, OPTION_QUEUE_TIMEOUT[1]),
        )


##### Main #####
if __name__ == "__main__":
    SplitterMain(
        apps.splitter.Splitter,
        SPLITTER_SECTION,
        (OPTION_QUEUE_TIMEOUT,),
        (ARG_QUEUE_TIMEOUT,),
    ).run()

