#!/usr/bin/env pypy3


import raava.rules
import raava.handlers
import raava.apps.splitter
import gns.const
import gns.service
import gns.stub


##### Public classes #####
class SplitterMain(gns.service.AbstractMain):
    def __init__(self):
        gns.service.AbstractMain.__init__(
            self,
            raava.apps.splitter.Splitter,
            gns.service.SECTION.SPLITTER,
            (
                gns.service.OPTION_RULES_DIR,
                gns.service.OPTION_QUEUE_TIMEOUT,
            ),
            (
                gns.service.ARG_RULES_DIR,
                gns.service.ARG_QUEUE_TIMEOUT,
            ),
            gns.const.CONFIG_FILE,
        )

    def construct(self, options):
        raava.rules.setup_builtins(gns.stub.MATCHER_BUILTINS_MAP)
        hstorage = raava.handlers.Handlers(
            options[gns.service.OPTION_RULES_DIR],
            (
                gns.stub.HANDLER.ON_EVENT,
                gns.stub.HANDLER.ON_NOTIFY,
                gns.stub.HANDLER.ON_SEND
            ),
        )
        hstorage.load_handlers()
        return (
            options[gns.service.OPTION_ZOO_NODES],
            hstorage,
            options[gns.service.OPTION_QUEUE_TIMEOUT],
        )


##### Main #####
if __name__ == "__main__":
    SplitterMain().run()

