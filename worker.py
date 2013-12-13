#!/usr/bin/env pypy3


from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from raava import service
from raava import rules

from raava import apps
import raava.apps.worker # pylint: disable=W0611

import gns


##### Public constants #####
WORKER_SECTION = "worker"
OPTION_QUEUE_TIMEOUT = ("queue-timeout", "queue_timeout", 1, lambda arg: validators.common.validNumber(arg, 0, value_type=float))
ARG_QUEUE_TIMEOUT = ((OPTION_QUEUE_TIMEOUT[0],), OPTION_QUEUE_TIMEOUT, { "action" : "store", "metavar" : "<seconds>" })


##### Public classes #####
class WorkerMain(service.Main):
    def construct(self, options):
        rules.setup_builtins(gns.WORKER_BUILTINS_MAP)
        return (
            options[service.OPTION_ZOO_NODES],
            options[OPTION_QUEUE_TIMEOUT],
        )


##### Main #####
if __name__ == "__main__":
    WorkerMain(
        apps.worker.Worker,
        WORKER_SECTION,
        (OPTION_QUEUE_TIMEOUT,),
        (ARG_QUEUE_TIMEOUT,),
    ).run()

