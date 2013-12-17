@match_event(host=regexp(r"bar\d+"), level=in_list(LEVEL.CRIT, LEVEL.WARN))
def on_event(event) :
    notify(event, user="mdevaev", wait=5)
    notify(event, user="nbryskin")

