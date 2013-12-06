#!/usr/bin/env pypy3

import time

from raava import zoo
from raava import worker
from raava import rules

import gns

gns.init_logging()
rules.setup_builtins(gns.WORKER_BUILTINS_MAP)
z = zoo.connect(("localhost",))
zoo.init(z)
worker_thread = worker.WorkerThread(z, 1)
worker_thread.start()
try:
    worker_thread.join()
except KeyboardInterrupt:
    worker_thread.stop()
    for _ in range(10):
        if worker_thread.alive_children() == 0:
            break
        time.sleep(1)
    rules.cleanup_builtins()

