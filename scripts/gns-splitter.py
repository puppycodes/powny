#!/usr/bin/env python


from raava import handlers
from raava import application
from raava import splitter

from gns import service
from gns import zclient
from gns import core
from gns import chain


##### Public methods #####
def main():
    config = service.init(description="GNS Splitter")[0]
    core_attrs = config[service.S_CORE]
    app_attrs = config[service.S_SPLITTER]

    core.init_rules_environment(config)

    loader = handlers.Loader(
        core_attrs[service.O_RULES_DIR],
        core_attrs[service.O_RULES_HEAD],
        (
            chain.HANDLER.ON_EVENT,
            chain.HANDLER.ON_NOTIFY,
            chain.HANDLER.ON_SEND,
        ),
    )

    app = application.Application(
        thread_class  = splitter.SplitterThread,
        zoo_connect   = lambda: zclient.connect(config),
        workers       = app_attrs[service.O_WORKERS],
        die_after     = app_attrs[service.O_DIE_AFTER],
        quit_wait     = app_attrs[service.O_QUIT_WAIT],
        interval      = app_attrs[service.O_RECHECK],
        loader        = loader,
        queue_timeout = app_attrs[service.O_QUEUE_TIMEOUT],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

