#!/usr/bin/env pypy3


import raava.rules
import raava.handlers
import raava.apps.worker

import gns.service
import gns.stub


##### Public methods #####
def main():
    options = gns.service.parse_options(
        app_section="worker",
        args_list=(
            gns.service.ARG_RULES_DIR,
            gns.service.ARG_QUEUE_TIMEOUT,
        ),
    )
    gns.service.init_logging(options)

    raava.rules.setup_builtins(gns.stub.WORKER_BUILTINS_MAP)
    raava.handlers.setup_path(options[gns.service.OPTION_RULES_DIR])

    app = raava.apps.worker.Worker(
        workers=options[gns.service.OPTION_WORKERS],
        die_after=options[gns.service.OPTION_DIE_AFTER],
        quit_wait=options[gns.service.OPTION_QUIT_WAIT],
        interval=options[gns.service.OPTION_INTERVAL],
        host_list=options[gns.service.OPTION_ZOO_NODES],
        queue_timeout=options[gns.service.OPTION_QUEUE_TIMEOUT],
        rules_path=options[gns.service.OPTION_RULES_DIR],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

