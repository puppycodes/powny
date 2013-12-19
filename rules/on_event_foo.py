@match_event(host="foo")
def on_event(event) :
    notify(event, user="mdevaev", wait=10)
    notify(event, user="nbryskin")

