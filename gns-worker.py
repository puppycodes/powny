#!/usr/bin/env pypy3


from raava import service
from raava import rules

from raava import apps
import raava.apps.worker # pylint: disable=W0611

import gns


##### Public classes #####
class WorkerMain(service.AbstractMain):
    def __init__(self):
        service.AbstractMain.__init__(
            self,
            apps.worker.Worker,
            service.SECTION.WORKER,
            (service.OPTION_QUEUE_TIMEOUT,),
            (service.ARG_QUEUE_TIMEOUT,),
        )
    def construct(self, options):
        rules.setup_builtins(gns.WORKER_BUILTINS_MAP)
        return (
            options[service.OPTION_ZOO_NODES],
            options[service.OPTION_QUEUE_TIMEOUT],
        )


##### Main #####
if __name__ == "__main__":
    WorkerMain().run()

