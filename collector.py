#!/usr/bin/env pypy3


from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from raava import service

from raava import apps
import raava.apps.collector # pylint: disable=W0611


##### Public constants #####
COLLECTOR_SECTION = "worker"

OPTION_POLL_INTERVAL     = ("poll-interval",     "poll_interval",     10, lambda arg: validators.common.validNumber(arg, 1))
OPTION_ACQUIRE_DELAY     = ("acquire-delay",     "acquire_delay",     5,  lambda arg: validators.common.validNumber(arg, 1))
OPTION_RECYCLED_PRIORITY = ("recycled-priority", "recycled_priority", 0,  lambda arg: validators.common.validNumber(arg, 0))

ARG_POLL_INTERVAL     = ((OPTION_POLL_INTERVAL[0],),   OPTION_POLL_INTERVAL,     { "action" : "store", "metavar" : "<seconds>" })
ARG_ACQUIRE_DELAY     = ((OPTION_ACQUIRE_DELAY[0],),   OPTION_ACQUIRE_DELAY,     { "action" : "store", "metavar" : "<seconds>" })
ARG_RECYCLED_PRIORITY = ((OPTION_RECYCLED_PRIORITY[0], OPTION_RECYCLED_PRIORITY, { "action" : "store", "metavar" : "<number>" }))


##### Public classes #####
class CollectorMain(service.Main):
    def construct(self, options):
        return (
            options[service.OPTION_ZOO_NODES],
            options[OPTION_POLL_INTERVAL],
            options[OPTION_ACQUIRE_DELAY],
            options[OPTION_RECYCLED_PRIORITY],
        )


##### Main #####
if __name__ == "__main__":
    CollectorMain(
        apps.collector.Collector,
        COLLECTOR_SECTION,
        (
            OPTION_POLL_INTERVAL,
            OPTION_ACQUIRE_DELAY,
            OPTION_RECYCLED_PRIORITY,
        ),
        (
            ARG_POLL_INTERVAL,
            ARG_ACQUIRE_DELAY,
            ARG_RECYCLED_PRIORITY,
        ),
    ).run()

