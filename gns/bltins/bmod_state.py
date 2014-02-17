import decorator
import pickle
from ulib import typetools

from raava import zoo

from .. import service
from .. import env


##### Private constants #####
class _STATE:
    PREV = "prev"


##### Private methods #####
def _save_prev(*fields):
    fields = sorted(fields or ("host_name", "service_name"))
    def make_method(method):
        def wrap(method, event_root):
            zoo_nodes = env.get_config(service.S_CORE, service.O_ZOO_NODES)
            check_id = typetools.object_hash([ event_root.get(field) for field in fields ])
            check_path = zoo.join("/state", check_id)

            with zoo.Connect(zoo_nodes) as client:
                try:
                    client.create(check_path, pickle.dumps(None), makepath=True)
                except zoo.NodeExistsError:
                    pass
                prev_event = client.pget(check_path)

            event_root.get_extra()[_STATE.PREV] = prev_event
            try:
                return method(event_root)
            finally:
                with zoo.Connect(zoo_nodes) as client:
                    prev_event = event_root.copy()
                    if _STATE.PREV in prev_event.get_extra():
                        del prev_event.get_extra()[_STATE.PREV]
                    client.pset(check_path, prev_event)

        return decorator.decorator(wrap, method)
    return make_method

def _field_is_changed(event_root, prev, current, field = "status"):
    prev_event = event_root.get_extra().get(_STATE.PREV)
    if prev_event is None:
        return True

    is_changed = (
        (prev is None or ( prev is not None and prev == prev_event.get(field) )) and
        (current is None or ( current is not None and current == event_root.get(field) )) and
        prev_event[field] != event_root[field]
    )
    return is_changed


##### Private classes #####
class _State:
    save_prev = _save_prev
    is_changed = _field_is_changed


##### Public constants #####
BUILTINS_MAP = {
    "state": _State,
}

