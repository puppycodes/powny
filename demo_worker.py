#!/usr/bin/env pypy3

import time

from raava import const
from raava import zoo
from raava import worker
from raava import rules


def notify(task, *args_tuple, **kwargs_dict):
    task.checkpoint()
    print(args_tuple, kwargs_dict)
    time.sleep(2)
    task.checkpoint()

worker.setup_builtins({
        "notify"     : notify,
    })

import builtins
builtins.match_event = rules.match_event

import logging
logger = logging.getLogger(const.LOGGER_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(name)s %(threadName)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

z = zoo.connect(("localhost",))
zoo.init(z)

worker_thread = worker.Worker(z, 1, 5, 5)
worker_thread.start()
worker_thread.join()

