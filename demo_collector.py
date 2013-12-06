#!/usr/bin/env pypy3

from raava import zoo
from raava import collector

import gns

gns.init_logging()
z = zoo.connect(("localhost",))
zoo.init(z)
collector_thread = collector.CollectorThread(z, 0.01, 5, 0)
collector_thread.start()
try:
    collector_thread.join()
except KeyboardInterrupt:
    collector_thread.stop()

