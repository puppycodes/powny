import re


# =====
def get_from_path(event, path):
    if isinstance(path, str):
        path = tuple(filter(None, path.split(".")))
    assert len(path) > 0, "Required not empty path for event fields"
    for part in path:
        event = event[part]
    return event  # As value

def _make_cmp(name, method):
    class comparator:  # pylint: disable=invalid-name
        def __init__(self, path, *args):
            self._path = path
            self._args = args

        def __repr__(self):
            return "<cmp::{name}(path={path}; args={args})>".format(
                name=self.__class__.__name__,
                path=repr(self._path),
                args=repr(self._args),
            )

        def __call__(self, event):
            return method(get_from_path(event, self._path), *self._args)

    comparator.__name__ = name
    return comparator


# pylint: disable=invalid-name
eq = equal          = _make_cmp("equal",          lambda operand, value: value == operand)
ne = not_equal      = _make_cmp("not_equal",      lambda operand, value: value != operand)
ge = great_or_equal = _make_cmp("great_or_equal", lambda operand, value: value >= operand)
gt = great          = _make_cmp("great",          lambda operand, value: value > operand)
le = less_or_equal  = _make_cmp("less_or_equal",  lambda operand, value: value <= operand)
lt = less           = _make_cmp("less",           lambda operand, value: value < operand)
is_none     = _make_cmp("is_none",     lambda operand: operand is None)
is_not_none = _make_cmp("is_not_none", lambda operand: operand is not None)
in_list     = _make_cmp("in_list",     lambda operand, value: value in operand)
not_in_list = _make_cmp("not_in_list", lambda operand, value: value not in operand)
regexp      = _make_cmp("regexp",      lambda operand, rx: re.match(rx, str(operand)) is not None)
