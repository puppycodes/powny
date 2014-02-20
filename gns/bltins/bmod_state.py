# required:
#   - bmod_const
#   - bmod_storage


import builtins

from ulib import typetools

from raava import zoo


##### Private methods #####
def _add_previous(*fields):
    fields = sorted( fields or (
            builtins.EVENT.HOST, # pylint: disable=E1101
            builtins.EVENT.SERVICE, # pylint: disable=E1101
        ))
    def make_method(method):
        def wrap(event_root, **kwargs):
            kwargs = {}
            check_id = typetools.object_hash([ event_root.get(field) for field in fields ])
            check_path = zoo.join("_state", check_id)
            kwargs["previous"] = builtins.storage.get(check_path, None) # pylint: disable=E1101
            try:
                result = method(event_root, **kwargs)
            finally:
                builtins.storage.set(check_path, event_root) # pylint: disable=E1101
            return result
        return wrap
    return make_method

def _is_changed(previous, current, from_, to, field = builtins.EVENT.STATUS): # pylint: disable=E1101
    if previous is None:
        return True
    is_changed = (
        (from_ is None or ( from_ is not None and from_ == previous.get(field) )) and
        (to is None or ( to is not None and to == current.get(field) )) and
        previous[field] != current[field]
    )
    return is_changed


##### Private classes #####
class _State:
    add_previous = _add_previous
    is_changed = _is_changed


##### Public constants #####
BUILTINS_MAP = {
    "state": _State,
}

