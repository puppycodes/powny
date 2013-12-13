#!/usr/bin/env pypy3

import sys

from raava import zoo
from raava import events

import gns

gns.init_logging()
z = zoo.connect(["localhost"])
zoo.init(z)
events.cancel_event(z, sys.argv[1])
