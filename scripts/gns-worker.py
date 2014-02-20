#!/usr/bin/env python


from raava import rhooks
from raava import handlers
from raava import application
from raava import worker

from gns import service
from gns import bltins
from gns import env


##### Public methods #####
def main():
    config_dict = service.init(description="GNS Worker")[0]
    core_dict = config_dict[service.S_CORE]
    app_dict = config_dict[service.S_WORKER]

    rhooks.setup_builtins(bltins.load_builtins(config_dict))
    env.setup_config(config_dict)
    handlers.setup_path(core_dict[service.O_RULES_DIR])

    app = application.Application(
        thread_class  = worker.WorkerThread,
        workers       = app_dict[service.O_WORKERS],
        die_after     = app_dict[service.O_DIE_AFTER],
        quit_wait     = app_dict[service.O_QUIT_WAIT],
        interval      = app_dict[service.O_RECHECK],
        nodes_list    = core_dict[service.O_ZOO_NODES],
        queue_timeout = app_dict[service.O_QUEUE_TIMEOUT],
        rules_path    = core_dict[service.O_RULES_DIR],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

