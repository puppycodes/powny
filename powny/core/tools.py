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
def get_node_name():
    return platform.uname()[1]


def get_version():
    pkg = pkginfo.get_metadata("powny")
    return (pkg.version if pkg is not None else "<unknown>")


def get_user_agent():
    return "Powny/{}".format(get_version())


# =====
def make_isotime(unix=None):  # ISO 8601
    if unix is None:
        unix = time.time()
    return datetime.datetime.utcfromtimestamp(unix).strftime("%Y-%m-%d %H:%M:%S.%fZ")


def from_isotime(line):
    dt = dateutil.parser.parse(line)
    return calendar.timegm(dt.utctimetuple()) + dt.microsecond / 10 ** 6  # pylint: disable=maybe-no-member


# =====
def make_loader(rules_root):
    return imprules.Loader(
        prefix=rules_root,
        group_by=(
            ("handlers", rules.is_event_handler),
            ("methods", lambda _: True),
        ),
    )


def get_exposed(backend, loader):
    head = backend.rules.get_head()
    exposed = None
    errors = None
    exc = None
    if head is not None:
        try:
            (exposed, errors) = loader.get_exposed(head)
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
