#!/usr/bin/env pypy3


from raava import service

from raava import apps
import raava.apps.collector # pylint: disable=W0611


##### Public classes #####
class CollectorMain(service.AbstractMain):
    def __init__(self):
        service.AbstractMain.__init__(
            self,
            apps.collector.Collector,
            service.SECTION.COLLECTOR,
            (
                service.OPTION_POLL_INTERVAL,
                service.OPTION_ACQUIRE_DELAY,
                service.OPTION_RECYCLED_PRIORITY,
            ),
            (
                service.ARG_POLL_INTERVAL,
                service.ARG_ACQUIRE_DELAY,
                service.ARG_RECYCLED_PRIORITY,
            ),
        )

    def construct(self, options):
        return (
            options[service.OPTION_ZOO_NODES],
            options[service.OPTION_POLL_INTERVAL],
            options[service.OPTION_ACQUIRE_DELAY],
            options[service.OPTION_RECYCLED_PRIORITY],
        )


##### Main #####
if __name__ == "__main__":
    CollectorMain().run()

