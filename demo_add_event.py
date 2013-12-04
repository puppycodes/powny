#!/usr/bin/env pypy3

import json

from raava import zoo
from raava import rules
from raava import events

events_api = events.EventsApi(zoo.connect(["localhost"]))
event_root = rules.EventRoot(json.loads(input()), extra={ rules.EXTRA_HANDLER : rules.HANDLER.ON_EVENT })
print(events_api.add_event(event_root))
