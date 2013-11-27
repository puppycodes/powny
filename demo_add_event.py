#!/usr/bin/env pypy3

from raava import zoo
from raava import events

events_api = events.EventsApi(zoo.connect(["localhost"]))
events_api.add_event(input())
