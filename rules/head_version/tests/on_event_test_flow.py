from . import echo_event

@match_event(host="test_flow")
def on_event(event):
    echo_event(event)

