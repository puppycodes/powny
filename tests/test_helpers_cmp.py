# pylint: disable=R0904
# pylint: disable=W0212


import pytest

from powny.helpers import cmp


# =====
_EVENT = {"a": {"b": {
    "c":       1,
    "none":    None,
    "list":    [1, 2, 3],
    "host":    "foo42",
    "service": 13,
}}}


# =====
def test_repr_and_str():
    for to in (str, repr):
        assert to(cmp.equal("a.b.c", 1)) == "<cmp::equal(path='a.b.c'; args=(1,))>"


class TestGetFromPath:
    def test_str(self):
        assert cmp.get_from_path(_EVENT, "a.b.c") == 1

    def test_str_extra(self):
        assert cmp.get_from_path(_EVENT, "a.b...c.") == 1

    def test_str_empty(self):
        with pytest.raises(AssertionError):
            cmp.get_from_path(_EVENT, ".")

    def test_str_key_error(self):
        with pytest.raises(KeyError):
            cmp.get_from_path(_EVENT, "a.foo")

    def test_list(self):
        assert cmp.get_from_path(_EVENT, ["a", "b", "c"]) == 1

    def test_list_empty(self):
        with pytest.raises(AssertionError):
            cmp.get_from_path(_EVENT, [])

    def test_list_key_error(self):
        with pytest.raises(KeyError):
            cmp.get_from_path(_EVENT, ["a", "foo"])


class TestComparators:
    def test_equal(self):
        assert cmp.equal("a.b.c", -1)(_EVENT) == False
        assert cmp.equal("a.b.c", 1)(_EVENT) == True
        assert cmp.equal("a.b.c", 0)(_EVENT) == False

    def test_not_equal(self):
        assert cmp.not_equal("a.b.c", -1)(_EVENT) == True
        assert cmp.not_equal("a.b.c", 0)(_EVENT) == True
        assert cmp.not_equal("a.b.c", 1)(_EVENT) == False

    def test_great_or_equal(self):
        assert cmp.great_or_equal("a.b.c", 0)(_EVENT) == False
        assert cmp.great_or_equal("a.b.c", 1)(_EVENT) == True
        assert cmp.great_or_equal("a.b.c", 2)(_EVENT) == True

    def test_great(self):
        assert cmp.great("a.b.c", 2)(_EVENT) == True
        assert cmp.great("a.b.c", 1)(_EVENT) == False
        assert cmp.great("a.b.c", 0)(_EVENT) == False

    def test_less_or_equal(self):
        assert cmp.less_or_equal("a.b.c", 0)(_EVENT) == True
        assert cmp.less_or_equal("a.b.c", 1)(_EVENT) == True
        assert cmp.less_or_equal("a.b.c", 2)(_EVENT) == False

    def test_less(self):
        assert cmp.less("a.b.c", 0)(_EVENT) == True
        assert cmp.less("a.b.c", 1)(_EVENT) == False
        assert cmp.less("a.b.c", 2)(_EVENT) == False

    def test_is_none(self):
        assert cmp.is_none("a.b.none")(_EVENT) == True
        assert cmp.is_none("a.b.c")(_EVENT) == False

    def test_is_not_none(self):
        assert cmp.is_not_none("a.b.c")(_EVENT) == True
        assert cmp.is_not_none("a.b.none")(_EVENT) == False

    def test_in_list(self):
        assert cmp.in_list("a.b.list", 2)(_EVENT) == True
        assert cmp.in_list("a.b.list", 5)(_EVENT) == False

    def test_not_in_list(self):
        assert cmp.not_in_list("a.b.list", 5)(_EVENT) == True
        assert cmp.not_in_list("a.b.list", 2)(_EVENT) == False

    def test_regexp(self):
        assert cmp.regexp("a.b.host", r"foo\d+")(_EVENT) == True
        assert cmp.regexp("a.b.host", r"bar\d+")(_EVENT) == False
        assert cmp.regexp("a.b.service", r"13")(_EVENT) == True
