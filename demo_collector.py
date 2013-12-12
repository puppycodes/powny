#!/usr/bin/env pypy3

from raava import zoo
from raava import application

from raava import apps
import raava.apps.collector # pylint: disable=W0611

def main():
    application.init_logging()

    client = zoo.connect(["localhost"])
    zoo.init(client)
    client.stop()

    apps.collector.Collector(10, 100, 10, 0.01, (["localhost"], 0.01, 5, 0)).run()

if __name__ == "__main__":
    main()

