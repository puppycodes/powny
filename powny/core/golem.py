import json
import functools

from ulib.validators.common import valid_bool

from contextlog import get_logger


# =====
OK = "OK"
WARN = "WARN"
CRIT = "CRIT"


_ATTR_ON_EVENT = "_golem_on_event"
_ATTR_MATCHERS = "_golem_matchers"


# =====
def on_event(method):
    @functools.wraps(method)
    def wrap(previous, current):
        return method((previous and Event(previous)), Event(current))
    setattr(wrap, _ATTR_ON_EVENT, True)
    if hasattr(method, _ATTR_MATCHERS):
        setattr(wrap, _ATTR_MATCHERS, getattr(method, _ATTR_MATCHERS))
    return wrap


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


def check_match(method, previous, current):
    previous = (previous and Event(previous))
    current = Event(current)
    for matcher in getattr(method, _ATTR_MATCHERS, []):
        logger = get_logger(
            method="{}.{}".format(method.__module__, method.__name__),
            previous_event=(previous and previous.get_minimal()),
            current_event=current.get_minimal(),
        )
        try:
            if not matcher(previous, current):
                logger.debug("Event is not matched by %s", matcher)
                return False
        except Exception:
            logger.exception("Matching error matcher %s", matcher)
            return False
    return True


# =====
class IncorrectEventError(Exception):
    pass


# =====
class Event:
    # TODO: Make objects for children

    def __init__(self, raw_event):
        self._raw = raw_event.copy()

    def get_raw(self):
        return self._raw

    def get_minimal(self):
        return {
            "host": self.host,  # pylint: disable=no-member
            "service": self.service,  # pylint: disable=no-member
            "status": self.status,  # pylint: disable=no-member
            "description": self.description,  # pylint: disable=no-member
        }


# http://stackoverflow.com/questions/1454984/how-to-define-properties-in-init
for key in (
    "host", "service", "instance",
    "status", "summary", "description",
    "truncated_up_to", "children", "aggregator", "counts",
):
    setattr(Event, key, property(
        lambda self, key=key: self.get_raw().get(key)
    ))


# =====
def convert_status(golem_status):
    # Case-insensitive cruthch:
    #   ok -> OK
    #   crit, critical -> CRIT
    #   warn, warning -> WARN
    status = golem_status.upper()
    status = {"WARNING": WARN, "CRITICAL": CRIT}.get(status, status)
    if status not in (OK, WARN, CRIT):
        raise IncorrectEventError("Invalid status: {}".format(golem_status))
    return status


def convert_golem_event(data):
    # See ya-wiki: sm/obsolete/protocols/JsonDescription
    _check_required_fields(data, ("object", "eventtype"))
    raw_event = {
        "host": data["object"],
        "service": data["eventtype"],
    }
    if valid_bool(data.get("json", False)):
        raw_event.update(json.loads(data.get("info", "{}")))
        _check_required_fields(raw_event, ("status", "description"))
    else:
        raw_event["status"] = convert_status(data.get("status", "critical"))
        raw_event["description"] = data.get("info", "")
    return raw_event


def _check_required_fields(data, fields):
    missing = set(fields).difference(set(data))
    if len(missing) != 0:
        raise IncorrectEventError("Missing required fields: {}".format(", ".join(missing)))
