#!/usr/bin/env pypy3


import raava.apps.collector
import gns.const
import gns.service


##### Public classes #####
class CollectorMain(gns.service.AbstractMain):
    def __init__(self):
        gns.service.AbstractMain.__init__(
            self,
            raava.apps.collector.Collector,
            gns.service.SECTION.COLLECTOR,
            (
                gns.service.OPTION_POLL_INTERVAL,
                gns.service.OPTION_ACQUIRE_DELAY,
                gns.service.OPTION_RECYCLED_PRIORITY,
                gns.service.OPTION_GARBAGE_LIFETIME,
            ),
            (
                gns.service.ARG_POLL_INTERVAL,
                gns.service.ARG_ACQUIRE_DELAY,
                gns.service.ARG_RECYCLED_PRIORITY,
                gns.service.ARG_GARBAGE_LIFETIME,
            ),
            gns.const.CONFIG_FILE,
        )

    def construct(self, options):
        return (
            options[gns.service.OPTION_ZOO_NODES],
            options[gns.service.OPTION_POLL_INTERVAL],
            options[gns.service.OPTION_ACQUIRE_DELAY],
            options[gns.service.OPTION_RECYCLED_PRIORITY],
            options[gns.service.OPTION_GARBAGE_LIFETIME],
        )


##### Main #####
if __name__ == "__main__":
    CollectorMain().run()

