from . import echo_event

@match_event(host="test_state")
@state.add_previous(EVENT.HOST)
def on_event(event, previous):
    echo_event(event, previous)

