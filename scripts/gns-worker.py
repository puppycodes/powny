#!/usr/bin/env python


from raava import application
from raava import worker

from gns import service
from gns import core


##### Public methods #####
def main():
    config = service.init(description="GNS Worker")[0]
    core_attrs = config[service.S_CORE]
    app_attrs = config[service.S_WORKER]

    core.init_rules_environment(config)

    app = application.Application(
        thread_class  = worker.WorkerThread,
        workers       = app_attrs[service.O_WORKERS],
        die_after     = app_attrs[service.O_DIE_AFTER],
        quit_wait     = app_attrs[service.O_QUIT_WAIT],
        interval      = app_attrs[service.O_RECHECK],
        nodes_list    = core_attrs[service.O_ZOO_NODES],
        queue_timeout = app_attrs[service.O_QUEUE_TIMEOUT],
        rules_path    = core_attrs[service.O_RULES_DIR],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

