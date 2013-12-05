#!/usr/bin/env pypy3

from raava import const
from raava import zoo
from raava import splitter
from raava import rules
from raava import handlers

import gns

import logging
logger = logging.getLogger(const.LOGGER_NAME)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("%(name)s %(threadName)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

rules.setup_builtins({
        "LEVEL":       gns.LEVEL,
        "match_event": rules.match_event,
    })

hand = handlers.Handlers("demo", (gns.HANDLER.ON_EVENT, gns.HANDLER.ON_NOTIFY, gns.HANDLER.ON_SEND))
hand.load_handlers()
splitter_thread = splitter.SplitterThread(
    zoo.connect(("localhost",)),
    hand,
    1,
)
splitter_thread.start()
splitter_thread.join()

