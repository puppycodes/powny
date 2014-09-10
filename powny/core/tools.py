import os

import pkginfo

from contextlog import get_logger

from . import context
from . import imprules
from . import rules


# =====
def get_powny_version():
    try:
        pkg = pkginfo.get_metadata("powny")
    except AttributeError:
        # FIXME: Crutch for namespace packages on Python 3.2
        #  File "/opt/pypy3/site-packages/pkginfo/installed.py", line 29, in read
        #    package = self.package.__package__
        #  AttributeError: 'module' object has no attribute '__package__'
        return None
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

def get_dumped_method(name, kwargs, exposed):
    method = exposed.get("methods", {}).get(name)
    if method is None:
        return None
    else:
        return context.dump_call(method, kwargs)

def get_dumped_handlers(kwargs, exposed):
    return {
        name: context.dump_call(handler, kwargs)
        for (name, handler) in exposed.get("handlers", {}).items()
        if rules.check_match(handler, kwargs)
    }
