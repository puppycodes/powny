import os
import pickle

import pkginfo

from contextlog import get_logger

from . import imprules
from . import rules


# =====
def get_powny_version():
    pkg = pkginfo.get_metadata("powny")
    return (pkg.version if pkg is not None else None)

def make_rules_path(rules_root, head):
    return os.path.join(rules_root, head)

def make_loader(rules_base):
    return imprules.Loader(
        module_base=rules_base,
        group_by=(
            ("handlers", rules.is_event_handler),
            ("methods",  lambda _: True),
        ),
    )

def get_exposed(backend, loader, rules_root):
    head = backend.rules.get_head()
    exposed = None
    errors = None
    exc = None
    if head is not None:
        try:
            (exposed, errors) = loader.get_exposed(make_rules_path(rules_root, head))
        except Exception as err:
            exc = "{}: {}".format(type(err).__name__, err)
            get_logger().exception("Can't load HEAD '%s'", head)
    return (head, exposed, errors, exc)

def get_func_method(name, exposed):
    method = exposed.get("methods", {}).get(name)
    if method is None:
        return None
    else:
        return pickle.dumps(method)

def get_func_handlers(kwargs, exposed):
    return {
        name: pickle.dumps(handler)
        for (name, handler) in exposed.get("handlers", {}).items()
        if rules.check_match(handler, kwargs)
    }
