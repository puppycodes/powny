from powny.core import golem


# =====
def test_on_event():
    @golem.on_event
    @golem.on_event
    def handler():
        pass
    assert golem.is_event_handler(handler)
    assert golem.is_event_handler(golem.on_event(lambda: None))

    def method():
        pass
    assert not golem.is_event_handler(method)
    assert not golem.is_event_handler(lambda: None)


def test_check_match():
    @golem.on_event
    @golem.match_event(lambda _, current: current.host == "foo")
    @golem.match_event(
        lambda _, current: current.service == "bar",
        lambda _, current: current.status == golem.OK,
    )
    def method():
        pass

    assert golem.check_match(method, None, {
        "host": "foo",
        "service": "bar",
        "status": golem.OK,
    })
    assert golem.check_match(method, None, {
        "host": "foo",
        "service": "bar",
        "status": golem.OK,
        "description": "Test",
    })
    assert not golem.check_match(method, None, {
        "host": "foo",
        "service": "bar",
        "status": golem.CRIT,
    })


def test_check_match_exception():
    def matcher(previous, _):
        assert previous is not None
        return True

    @golem.on_event
    @golem.match_event(matcher)
    def method():
        pass
    event = {"host": "foo", "service": "bar", "status": golem.OK}
    assert not golem.check_match(method, None, event)
    assert golem.check_match(method, event, event)
