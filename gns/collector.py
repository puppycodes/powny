from raava import application
from raava import appstate
from raava import collector
from raava import zoo

from gns import zclient
from gns import service


# =====
def run(config):
    app_opts = config[service.S_COLLECTOR]
    core_opts = config[service.S_CORE]
    zoo_connect = ( lambda: zclient.connect(config) )

    state_writer = appstate.StateWriter(
        zoo_connect = zoo_connect,
        state_base  = zoo.STATE_COLLECTOR,
        node_name   = core_opts[service.O_NODE_NAME],
    )

    app = application.Application(
        thread_class      = collector.CollectorThread,
        zoo_connect       = zoo_connect,
        workers           = app_opts[service.O_WORKERS],
        die_after         = app_opts[service.O_DIE_AFTER],
        quit_wait         = app_opts[service.O_QUIT_WAIT],
        interval          = app_opts[service.O_RECHECK],
        handle_signals    = core_opts[service.O_HANDLE_SIGNALS],
        state_writer      = state_writer,
        poll_interval     = app_opts[service.O_POLL_INTERVAL],
        delay             = app_opts[service.O_ACQUIRE_DELAY],
        recycled_priority = app_opts[service.O_RECYCLED_PRIORITY],
        garbage_lifetime  = app_opts[service.O_GARBAGE_LIFETIME],
    )
    app.run()
