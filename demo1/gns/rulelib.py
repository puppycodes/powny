import os
try :
    from enum import Enum
except ImportError :
    Enum = object
import importlib
import builtins


##### Public constants #####
class LEVEL(Enum) :
    CRIT   = 0
    WARN   = 1
    OK     = 2
    CUSTOM = 3

class URGENCY(Enum) :
    HIGH   = 0
    MEDIUM = 1
    LOW    = 2
    CUSTOM = 3

class HANDLERS(Enum) :
    ON_EVENT  = "on_event"
    ON_NOTIFY = "on_notify"

class FILTERS(Enum) :
    EVENT  = "event_filters_dict"
    EXTRA = "extra_filters_dict"


##### Public methods #####
def match_event(**filters_dict) :
    def make_method(method) :
        setattr(method, FILTERS.EVENT, filters_dict)
        return method
    return make_method

def match_extra(**filters_dict) :
    def make_method(method) :
        setattr(method, FILTERS.EXTRA, filters_dict)
        return method
    return make_method


###
def load_handlers(path) :
    on_event_set = set()
    on_notify_set = set()

    for (root_path, dirs_list, files_list) in os.walk(path, topdown=False) :
        root_path = root_path.replace(path, os.path.basename(path))
        for file_name in files_list :
            if file_name[0] in (".", "_") or not file_name.endswith(".py") :
                continue
            module_name = os.path.join(root_path, file_name)
            module_name = module_name[:module_name.index(".py")].replace("/", ".")
            module = importlib.import_module(module_name)

            if hasattr(module, HANDLERS.ON_EVENT) :
                on_event_set.add(getattr(module, HANDLERS.ON_EVENT))
            elif hasattr(module, HANDLERS.ON_NOTIFY) :
                on_notify_set.add(getattr(module, HANDLERS.ON_NOTIFY))

    return (on_event_set, on_notify_set)

def build_handlers(handlers_set, filters) :
    free_set = set()
    handlers_dict = {}
    for handler in handlers_set :
        filters_dict = getattr(handler, filters, None)
        if filters_dict is None :
            free_set.add(handler)
        else :
            for (key, values_list) in filters_dict.items() :
                handlers_dict.setdefault(key, {})
                if not isinstance(values_list, (tuple, list, set)) :
                    values_list = [values_list]
                for value in values_list :
                    handlers_dict[key].setdefault(value, set())
                    handlers_dict[key][value].add(handler)
    return (free_set, handlers_dict)

def h(l) :
    return list(map(lambda a : a.__module__, l))

def get_event_handlers(event, handlers_set) :#all_set, free_set, handlers_dict) :
    selected_set = set()
    for handler in handlers_set :
        if not hasattr(handler, FILTERS.EVENT) :
            selected_set.add(handler)
        else :
            filters_dict = getattr(handler, FILTERS.EVENT)
            for (key, value) in filters_dict.items() :
                if hasattr(event, key) and getattr(event, key) == value :
                    selected_set.add(handler)
    return selected_set


##### Public classes #####
class User :
    def __init__(self, name) :
        self.__name = name

    def send_email(self, event, **kwargs_dict) :
        print("    EMAIL: %s --- %s :: %s" % (self.__name, event, kwargs_dict))

    def send_sms(self, event, **kwargs_dict) :
        print("    SMS  : %s --- %s :: %s" % (self.__name, event, kwargs_dict))


##### FIXME #####
builtins.LEVEL = LEVEL
builtins.URGENCY = URGENCY
builtins.match_event = match_event
builtins.match_extra = match_extra

