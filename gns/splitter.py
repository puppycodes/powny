#!/usr/bin/env python


from raava import handlers
from raava import application
from raava import splitter
from raava import zoo

from gns import service
from gns import zclient
from gns import core
from gns import chain


# =====
def run(config):
    core_opts = config[service.S_CORE]
    app_opts = config[service.S_SPLITTER]

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

    def get_ext_stat():
        return {
            "loader": {
                "rules_dir": core_opts[service.O_RULES_DIR],
                "last_head": loader.get_last_head(),
            },
        }

    app = application.Application(
        thread_class  = splitter.SplitterThread,
        zoo_connect   = lambda: zclient.connect(config),
        state_base_path = zoo.STATE_SPLITTER_PATH,
        workers       = app_opts[service.O_WORKERS],
        die_after     = app_opts[service.O_DIE_AFTER],
        quit_wait     = app_opts[service.O_QUIT_WAIT],
        interval      = app_opts[service.O_RECHECK],
        handle_signals = core_opts[service.O_HANDLE_SIGNALS],
        loader        = loader,
        get_ext_stat  = get_ext_stat,
    )
    app.run()
