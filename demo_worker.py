#!/usr/bin/env pypy3

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
worker_thread.join()

