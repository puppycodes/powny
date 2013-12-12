#!/usr/bin/env pypy3

from raava import zoo
from raava import application
from raava import rules

from raava import apps
import raava.apps.worker

import gns

def main():
    application.init_logging()

    client = zoo.connect(["localhost"])
    zoo.init(client)
    client.stop()

    rules.setup_builtins(gns.WORKER_BUILTINS_MAP)
    apps.worker.Worker(10, 100, 10, 0.01, (["localhost"], 1)).run()

if __name__ == "__main__":
    main()

