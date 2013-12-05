#!/usr/bin/env pypy3

import sys

from raava import zoo
from raava import events

events_api = events.EventsApi(zoo.connect(["localhost"]))
events_api.cancel_event(sys.argv[1])
