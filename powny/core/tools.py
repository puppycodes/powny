import os
import socket
import platform
import datetime
import calendar
import time

import dateutil.parser
import pkginfo

from contextlog import get_logger

from . import context
from . import imprules
from . import rules


# =====
node_name = None
fqdn = None


def get_instance_info():
    return {
        "node": (node_name or platform.uname()[1]),
        "fqdn": (fqdn or socket.getfqdn()),
        "pid":  os.getpid(),
    }


def get_version():
    try:
        pkg = pkginfo.get_metadata("powny")
    except AttributeError:
        # FIXME: Crutch for namespace packages on Python 3.2
        #  File "/opt/pypy3/site-packages/pkginfo/installed.py", line 29, in read
        #    package = self.package.__package__
        #  AttributeError: 'module' object has no attribute '__package__'
        return None
    return (pkg.version if pkg is not None else None)


def get_user_agent():
    return "Powny/{version} from {fqdn}".format(
        version=(get_version() or "0.001"),  # FIXME: crutch for ^^^
        fqdn=get_instance_info()["fqdn"],
    )


# =====
def make_isotime(unix=None):  # ISO 8601
    if unix is None:
        unix = time.time()
    return datetime.datetime.utcfromtimestamp(unix).strftime("%Y-%m-%d %H:%M:%S.%fZ")


def from_isotime(line):
    dt = dateutil.parser.parse(line)
    return calendar.timegm(dt.utctimetuple()) + dt.microsecond / 10 ** 6  # pylint: disable=maybe-no-member


# =====
def make_rules_path(rules_root, head):
    return os.path.join(rules_root, head)


def make_loader(rules_base):
    return imprules.Loader(
        module_base=rules_base,
        group_by=(
            ("handlers", rules.is_event_handler),
            ("methods", lambda _: True),
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
