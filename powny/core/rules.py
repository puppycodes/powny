from contextlog import get_logger


# =====
_ATTR_ON_EVENT = "_powny_on_event"
_ATTR_MATCHERS = "_powny_matchers"


# =====
def on_event(method):
    setattr(method, _ATTR_ON_EVENT, True)
    return method

def is_event_handler(method):
    return getattr(method, _ATTR_ON_EVENT, False)

def match_event(*matchers):
    assert len(matchers) > 0, "Required minimum one matcher"

    def decorator(method):
        method_matchers = getattr(method, _ATTR_MATCHERS, [])
        for matcher in matchers:
            method_matchers.append(matcher)
        setattr(method, _ATTR_MATCHERS, method_matchers)
        return method

    return decorator

def check_match(method, event):
    for matcher in getattr(method, _ATTR_MATCHERS, []):
        logger = get_logger(func_name="{}.{}".format(method.__module__, method.__name__))
        try:
            if not matcher(event):
                logger.debug("Event is not matched by %s; data: %s", matcher, event)
                return False
        except Exception:
            logger.exception("Matching error with matcher %s; data: %s", matcher, event)
            return False
    return True
