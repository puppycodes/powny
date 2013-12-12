#!/usr/bin/env pypy3

from raava import zoo
from raava import rules
from raava import handlers
from raava import application

from raava import apps
import raava.apps.splitter # pylint: disable=W0611

import gns

def main():
    application.init_logging()

    client = zoo.connect(["localhost"])
    zoo.init(client)
    client.stop()

    rules.setup_builtins(gns.MATCHER_BUILTINS_MAP)
    hstorage = handlers.Handlers("demo", (gns.HANDLER.ON_EVENT, gns.HANDLER.ON_NOTIFY, gns.HANDLER.ON_SEND))
    hstorage.load_handlers()
    apps.splitter.Splitter(10, 100, 10, 0.01, (["localhost"], hstorage, 1)).run()
    rules.cleanup_builtins()

if __name__ == "__main__":
    main()

