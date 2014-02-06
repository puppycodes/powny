#!/usr/bin/env python


from raava import rules
from raava import handlers
from raava.apps.splitter import Splitter

from gns import service
from gns import bltins
from gns import chain
from gns import env


##### Public methods #####
def main():
    config_dict = service.init(description="GNS Splitter")[0]
    core_dict = config_dict[service.S_CORE]
    app_dict = config_dict[service.S_SPLITTER]

    rules.setup_builtins(bltins.load_builtins(config_dict))
    env.setup_config(config_dict)
    handlers.setup_path(core_dict[service.O_RULES_DIR])

    loader = handlers.Loader(
        core_dict[service.O_RULES_DIR],
        core_dict[service.O_RULES_HEAD],
        (
            chain.HANDLER.ON_EVENT,
            chain.HANDLER.ON_NOTIFY,
            chain.HANDLER.ON_SEND,
        ),
    )

    app = Splitter(
        workers       = app_dict[service.O_WORKERS],
        die_after     = app_dict[service.O_DIE_AFTER],
        quit_wait     = app_dict[service.O_QUIT_WAIT],
        interval      = app_dict[service.O_RECHECK],
        host_list     = core_dict[service.O_ZOO_NODES],
        loader        = loader,
        queue_timeout = app_dict[service.O_QUEUE_TIMEOUT],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

