#!/usr/bin/env pypy3


import raava.rules
import raava.handlers
import raava.apps.worker
import gns.const
import gns.service
import gns.stub


##### Public classes #####
def main():
    options = gns.service.init(
        app_section = gns.service.SECTION.WORKER,
        args_list = (
            gns.service.ARG_RULES_DIR,
            gns.service.ARG_QUEUE_TIMEOUT,
        ),
        config_file_path = gns.const.CONFIG_FILE
    )
    raava.rules.setup_builtins(gns.stub.WORKER_BUILTINS_MAP)
    raava.handlers.setup_path(options[gns.service.OPTION_RULES_DIR])

    app = raava.apps.worker.Worker(
        workers = options[gns.service.OPTION_WORKERS],
        die_after = options[gns.service.OPTION_DIE_AFTER],
        quit_wait = options[gns.service.OPTION_QUIT_WAIT],
        interval = options[gns.service.OPTION_INTERVAL],
        worker_args_tuple = (options[gns.service.OPTION_ZOO_NODES],
                             options[gns.service.OPTION_QUEUE_TIMEOUT])
    )
    app.run()

##### Main #####
if __name__ == "__main__":
    main()
