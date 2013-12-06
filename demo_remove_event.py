#!/usr/bin/env pypy3

import sys

from raava import zoo
from raava import events

import gns

gns.init_logging()
z = zoo.connect(["localhost"])
zoo.init(z)
events_api = events.EventsApi()
events_api.cancel_event(sys.argv[1])
