#!/usr/bin/env pypy3


from raava import service
from raava import rules
from raava import handlers

from raava import apps
import raava.apps.splitter # pylint: disable=W0611

import gns


##### Public classes #####
class SplitterMain(service.AbstractMain):
    def __init__(self):
        service.AbstractMain.__init__(
            self,
            apps.splitter.Splitter,
            service.SECTION.SPLITTER,
            (service.OPTION_QUEUE_TIMEOUT,),
            (service.ARG_QUEUE_TIMEOUT,),
        )

    def construct(self, options):
        rules.setup_builtins(gns.MATCHER_BUILTINS_MAP)
        hstorage = handlers.Handlers("demo", (gns.HANDLER.ON_EVENT, gns.HANDLER.ON_NOTIFY, gns.HANDLER.ON_SEND)) # FIXME: demo path
        hstorage.load_handlers()
        return (
            options[service.OPTION_ZOO_NODES],
            hstorage,
            options[service.OPTION_QUEUE_TIMEOUT],
        )


##### Main #####
if __name__ == "__main__":
    SplitterMain().run()

