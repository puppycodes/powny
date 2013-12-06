#!/usr/bin/env pypy3

from raava import zoo
from raava import splitter
from raava import rules
from raava import handlers

import gns

gns.init_logging()
rules.setup_builtins(gns.MATCHER_BUILTINS_MAP)
hand = handlers.Handlers("demo", (gns.HANDLER.ON_EVENT, gns.HANDLER.ON_NOTIFY, gns.HANDLER.ON_SEND))
hand.load_handlers()
z = zoo.connect(("localhost",))
zoo.init(z)
splitter_thread = splitter.SplitterThread(z, hand, 1)
splitter_thread.start()
try:
    splitter_thread.join()
except KeyboardInterrupt:
    splitter_thread.stop()
    rules.cleanup_builtins()

