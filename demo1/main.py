#!/usr/bin/env python3

import sys
import json
import copy
import builtins

import gns.rulelib
import gns.event


event_dict = json.loads(input())
event = gns.event.Event()
for (key, value) in event_dict.items() :
    setattr(event, key, value)
print("----- Input event -----\nDict: %s\nObject: %s" % (event_dict, list(filter(lambda arg : not arg.startswith("_"), dir(event)))))


(on_event_set, on_notify_set) = gns.rulelib.load_handlers("rules")
(free_on_event_set, on_event_dict) = gns.rulelib.build_handlers(on_event_set, gns.rulelib.FILTERS.EVENT)
(free_on_notify_set, on_notify_dict) = gns.rulelib.build_handlers(on_notify_set, gns.rulelib.FILTERS.EVENT)


def notify(event, **kwargs_dict) :
    event = copy.copy(event)
    handlers_set = gns.rulelib.get_event_handlers(event, on_notify_set)
    has_handler_flag = False
    for handler in handlers_set :
        if getattr(handler, gns.rulelib.FILTERS.EXTRA)["user"] == kwargs_dict["user"] :
            print("  notify", kwargs_dict, "->", handler.__module__+"."+handler.__name__)
            handler(event, gns.rulelib.User(kwargs_dict["user"]))
            has_handler_flag = True
    if not has_handler_flag :
        print("  notify", kwargs_dict, "->", "DEFAULT")
builtins.notify = notify


handlers_set = gns.rulelib.get_event_handlers(event, on_event_set)#, free_on_event_set, on_event_dict)
print("----- Trace -----")
for handler in handlers_set :
    print("event ->", handler.__module__+"."+handler.__name__)
    handler(copy.copy(event))

