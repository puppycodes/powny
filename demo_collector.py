#!/usr/bin/env pypy3

from raava import const
from raava import zoo
from raava import collector


import logging
logger = logging.getLogger(const.LOGGER_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(name)s %(threadName)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

z = zoo.connect(("localhost",))
zoo.init(z)

collector_thread = collector.CollectorThread(z, 0.01, 5, 0)
collector_thread.start()
collector_thread.join()

