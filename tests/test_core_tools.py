# pylint: disable=R0904
# pylint: disable=W0212
# pylint: disable=W0621


from powny.core import tools

from .fixtures.zookeeper import zbackend  # pylint: disable=W0611


# =====
def _get_exposed(backend, path, head=None):
    loader = tools.make_loader("rules")
    if head is not None:
        backend.rules.set_head(head)
    return tools.get_exposed(backend, loader, path)


# =====
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
    func = tools.get_func_method("rules.test.empty_method", exposed)
    assert isinstance(func, bytes)

def test_get_func_method_invalid(zbackend):
    exposed = _get_exposed(zbackend, "./rules", "0123456789abcdef")[1]
    func = tools.get_func_method("rules.test.test_method_not_found", exposed)
    assert func is None

def test_get_func_handlers(zbackend):
    exposed = _get_exposed(zbackend, "./rules", "0123456789abcdef")[1]
    funcs = tools.get_func_handlers({}, exposed)
    assert len(funcs) == 1
    assert isinstance(funcs["rules.test.empty_handler"], bytes)
