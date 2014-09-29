# pylint: disable=redefined-outer-name


import time

from powny.core import tools

from .fixtures.zookeeper import zbackend  # pylint: disable=unused-import
zbackend  # flake8 suppression pylint: disable=pointless-statement


# =====
def _get_exposed(backend, path, head=None):
    loader = tools.make_loader("rules")
    if head is not None:
        backend.rules.set_head(head)
    return tools.get_exposed(backend, loader, path)


# =====
def test_iso8601_funcs():
    now = int(time.time())
    assert tools.from_isotime(tools.make_isotime(now)) == now


def test_exposed_no_head(zbackend):
    (head, exposed, errors, exc) = _get_exposed(zbackend, "./rules")
    assert head is None
    assert exposed is None
    assert errors is None
    assert exc is None


def test_exposed_invalid_head(zbackend):
    test_head = "0"
    (head, exposed, errors, exc) = _get_exposed(zbackend, "./rules", test_head)
    assert head == test_head
    assert exposed is None
    assert errors is None
    assert isinstance(exc, str)


def test_exposed_ok(zbackend):
    test_head = "0123456789abcdef"
    (head, exposed, errors, exc) = _get_exposed(zbackend, "./rules", test_head)
    assert head == test_head
    assert len(exposed) > 0
    assert len(errors) > 0
    assert exc is None


def test_get_func_method(zbackend):
    exposed = _get_exposed(zbackend, "./rules", "0123456789abcdef")[1]
    state = tools.get_dumped_method("rules.test.empty_method", {}, exposed)
    assert isinstance(state, bytes)


def test_get_func_method_invalid(zbackend):
    exposed = _get_exposed(zbackend, "./rules", "0123456789abcdef")[1]
    state = tools.get_dumped_method("rules.test.test_method_not_found", {}, exposed)
    assert state is None


def test_get_func_handlers(zbackend):
    exposed = _get_exposed(zbackend, "./rules", "0123456789abcdef")[1]
    states = tools.get_dumped_handlers({}, exposed)
    assert len(states) == 1
    assert isinstance(states["rules.test.empty_handler"], bytes)
