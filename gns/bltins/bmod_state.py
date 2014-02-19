# required:
#   - bmod_const
#   - bmod_storage


import builtins

from ulib import typetools

from raava import zoo


##### Private methods #####
def _add_prev(*fields):
    fields = sorted( fields or (
            builtins.EVENT.HOST, # pylint: disable=E1101
            builtins.EVENT.SERVICE, # pylint: disable=E1101
        ))
    def make_method(method):
        def wrap(event_root, **kwargs):
            kwargs = {}
            check_id = typetools.object_hash([ event_root.get(field) for field in fields ])
            check_path = zoo.join("_state", check_id)
            kwargs["prev"] = builtins.storage.get(check_path, None) # pylint: disable=E1101
            try:
                result = method(event_root, **kwargs)
            finally:
                builtins.storage.set(check_path, event_root) # pylint: disable=E1101
            return result
        return wrap
    return make_method

def _is_changed(prev, current, frm, to, field = builtins.EVENT.STATUS): # pylint: disable=E1101
    if prev is None:
        return True
    is_changed = (
        (frm is None or ( frm is not None and frm == prev.get(field) )) and
        (to is None or ( to is not None and to == current.get(field) )) and
        prev[field] != current[field]
    )
    return is_changed


##### Private classes #####
class _State:
    add_prev = _add_prev
    is_changed = _is_changed


##### Public constants #####
BUILTINS_MAP = {
    "state": _State,
}

