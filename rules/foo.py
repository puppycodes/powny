@match_event(host="foo")
def on_event(event) :
    notify(event, user="andozer", wait=10)
    notify(event, user="asimakov", wait=10)
    notify(event, user="nbryskin")

