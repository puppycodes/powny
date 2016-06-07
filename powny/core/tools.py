import platform
import datetime
import calendar
import time

import dateutil.parser


# =====
def get_node_name():
    from .apps import get_config
    node_name = (get_config() or {}).get("core", {}).get("node_name")
    return (node_name or platform.uname()[1])


def get_version():
    return "4.5.0"


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
