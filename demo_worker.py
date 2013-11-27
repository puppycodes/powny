#!/usr/bin/env pypy3

import time

from raava import const
from raava import zoo
from raava import worker
from raava import rules


import logging
logger = logging.getLogger(const.LOGGER_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(name)s %(threadName)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

def notify(task, *args_tuple, **kwargs_dict):
    task.checkpoint()
    print(args_tuple, kwargs_dict)
    time.sleep(2)
    task.checkpoint()

rules.setup_builtins({
        "notify"     : worker.make_task_builtin(notify),
        "match_event": rules.match_event,
    })

z = zoo.connect(("localhost",))
zoo.init(z)

worker_thread = worker.Worker(z, 1, 5, 5)
worker_thread.start()
worker_thread.join()

