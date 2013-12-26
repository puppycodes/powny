#!/usr/bin/env pypy3


import raava.apps.collector
import gns.service


##### Public methods #####
def main():
    options = gns.service.parse_options(
        app_section="collector",
        args_list=(
            gns.service.ARG_POLL_INTERVAL,
            gns.service.ARG_ACQUIRE_DELAY,
            gns.service.ARG_RECYCLED_PRIORITY,
            gns.service.ARG_GARBAGE_LIFETIME,
        ),
    )

    gns.service.init_logging(options)

    app = raava.apps.collector.Collector(
        workers=options[gns.service.OPTION_WORKERS],
        die_after=options[gns.service.OPTION_DIE_AFTER],
        quit_wait=options[gns.service.OPTION_QUIT_WAIT],
        interval=options[gns.service.OPTION_INTERVAL],
        host_list=options[gns.service.OPTION_ZOO_NODES],
        poll_interval=options[gns.service.OPTION_POLL_INTERVAL],
        delay=options[gns.service.OPTION_ACQUIRE_DELAY],
        recycled_priority=options[gns.service.OPTION_RECYCLED_PRIORITY],
        garbage_lifetime=options[gns.service.OPTION_GARBAGE_LIFETIME],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

