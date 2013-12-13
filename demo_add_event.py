#!/usr/bin/env pypy3

import json

from raava import zoo
from raava import rules
from raava import events

import gns

gns.init_logging()
z = zoo.connect(["localhost"])
zoo.init(z)
event_root = rules.EventRoot(json.loads(input()))
print(events.add_event(z, event_root, gns.HANDLER.ON_EVENT))
