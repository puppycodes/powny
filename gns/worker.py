#!/usr/bin/env python


from raava import application
from raava import worker
from raava import zoo

from gns import service
from gns import zclient
from gns import core


# =====
def run(config):
    core_opts = config[service.S_CORE]
    app_opts = config[service.S_WORKER]

    core.init_rules_environment(config)

    app = application.Application(
        thread_class  = worker.WorkerThread,
        zoo_connect   = lambda: zclient.connect(config),
        state_base    = zoo.STATE_WORKER,
        workers       = app_opts[service.O_WORKERS],
        die_after     = app_opts[service.O_DIE_AFTER],
        quit_wait     = app_opts[service.O_QUIT_WAIT],
        interval      = app_opts[service.O_RECHECK],
        handle_signals = core_opts[service.O_HANDLE_SIGNALS],
        rules_path    = core_opts[service.O_RULES_DIR],
        node_name     = core_opts[service.O_NODE_NAME],
        process_name  = core_opts[service.O_PROCESS_NAME],
    )
    app.run()
