#!/usr/bin/env pypy3


import raava.rules
import raava.handlers
import raava.apps.worker
import gns.const
import gns.service
import gns.stub


##### Public classes #####
class WorkerMain(gns.service.AbstractMain):
    def __init__(self):
        gns.service.AbstractMain.__init__(
            self,
            raava.apps.worker.Worker,
            gns.service.SECTION.WORKER,
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
        raava.rules.setup_builtins(gns.stub.WORKER_BUILTINS_MAP)
        raava.handlers.setup_path(options[gns.service.OPTION_RULES_DIR])
        return (
            options[gns.service.OPTION_ZOO_NODES],
            options[gns.service.OPTION_QUEUE_TIMEOUT],
        )


##### Main #####
if __name__ == "__main__":
    WorkerMain().run()

