from raava import handlers
from raava import application
from raava import appstate
from raava import splitter
from raava import zoo

from gns import service
from gns import zclient
from gns import core
from gns import chain
from gns import fetcher


# =====
def run(config):
    core_opts = config[service.S_CORE]
    app_opts = config[service.S_SPLITTER]
    zoo_connect = ( lambda: zclient.connect(config) )

    core.init_rules_environment(config)

    loader = handlers.Loader(
        core_opts[service.O_RULES_DIR],
        core_opts[service.O_RULES_HEAD],
        (
            chain.HANDLER.ON_EVENT,
            chain.HANDLER.ON_NOTIFY,
            chain.HANDLER.ON_SEND,
        ),
    )

    def get_rules_info():
        last_head = loader.get_last_head()
        last_commit = ( last_head[len(fetcher.PREFIX):] if last_head is not None else None )
        return {
            "loader": {
                "rules_dir":   core_opts[service.O_RULES_DIR],
                "last_head":   last_head,
                "last_commit": last_commit,
            },
        }
    state_writer = appstate.StateWriter(
        zoo_connect = zoo_connect,
        state_base  = zoo.STATE_SPLITTER,
        node_name   = core_opts[service.O_NODE_NAME],
        get_ext     = get_rules_info,
    )

    app = application.Application(
        thread_class  = splitter.SplitterThread,
        zoo_connect   = zoo_connect,
        workers       = app_opts[service.O_WORKERS],
        die_after     = app_opts[service.O_DIE_AFTER],
        quit_wait     = app_opts[service.O_QUIT_WAIT],
        interval      = app_opts[service.O_RECHECK],
        handle_signals = core_opts[service.O_HANDLE_SIGNALS],
        state_writer  = state_writer,
        loader        = loader,
    )
    app.run()
