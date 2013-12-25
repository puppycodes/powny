#!/usr/bin/env pypy3


import raava.apps.collector
import gns.const
import gns.service


def main():
    options = gns.service.init(
        app_section = gns.service.SECTION.COLLECTOR,
        args_list = (
            gns.service.ARG_POLL_INTERVAL,
            gns.service.ARG_ACQUIRE_DELAY,
            gns.service.ARG_RECYCLED_PRIORITY,
            gns.service.ARG_GARBAGE_LIFETIME,
        ),
    )

    app = raava.apps.collector.Collector(
        workers = options[gns.service.OPTION_WORKERS],
        die_after = options[gns.service.OPTION_DIE_AFTER],
        quit_wait = options[gns.service.OPTION_QUIT_WAIT],
        interval = options[gns.service.OPTION_INTERVAL],
        worker_args_tuple = (options[gns.service.OPTION_ZOO_NODES],
                             options[gns.service.OPTION_POLL_INTERVAL],
                             options[gns.service.OPTION_ACQUIRE_DELAY],
                             options[gns.service.OPTION_RECYCLED_PRIORITY],
                             options[gns.service.OPTION_GARBAGE_LIFETIME])
    )
    app.run()


if __name__ == "__main__":
    main()
