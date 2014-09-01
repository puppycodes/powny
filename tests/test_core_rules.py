# pylint: disable=R0904
# pylint: disable=W0212


from powny.core import rules


# =====
def test_on_event():
    @rules.on_event
    def handler():
        pass
    assert rules.is_event_handler(handler)
    assert rules.is_event_handler(rules.on_event(lambda: None))

    def method():
        pass
    assert not rules.is_event_handler(method)
    assert not rules.is_event_handler(lambda: None)

def test_check_match():
    @rules.match_event(lambda kwargs: kwargs["x"] == 1)
    @rules.match_event(lambda kwargs: kwargs["y"] == 2, lambda kwargs: kwargs["z"] == 3)
    def method():
        pass
    assert rules.check_match(method, {"x": 1, "y": 2, "z": 3})
    assert rules.check_match(method, {"x": 1, "y": 2, "z": 3, "a": 5})
    assert not rules.check_match(method, {"x": 1, "y": 0, "z": 3})

def test_check_match_exception():
    def matcher(kwargs):
        if len(kwargs) == 0:
            raise RuntimeError
        return True

    @rules.match_event(matcher)
    def method():
        pass
    assert not rules.check_match(method, {})
    assert rules.check_match(method, {"x": 1})
