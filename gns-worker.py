#!/usr/bin/env python


from raava import rules
from raava import handlers
from raava.apps.worker import Worker

from gns import service
from gns import builts


##### Public methods #####
def main():
    config_dict = service.init(description="GNS Worker")[0]
    core_dict = config_dict[service.S_CORE]
    app_dict = config_dict[service.S_WORKER]

    rules.setup_builtins(builts.WORKER_BUILTINS_MAP)
    handlers.setup_path(core_dict[service.O_RULES_DIR])

    app = Worker(
        workers       = app_dict[service.O_WORKERS],
        die_after     = app_dict[service.O_DIE_AFTER],
        quit_wait     = app_dict[service.O_QUIT_WAIT],
        interval      = app_dict[service.O_RECHECK],
        host_list     = core_dict[service.O_ZOO_NODES],
        queue_timeout = app_dict[service.O_QUEUE_TIMEOUT],
        rules_path    = core_dict[service.O_RULES_DIR],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

