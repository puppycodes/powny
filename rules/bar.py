@match_event(host=regexp(r"bar\d+"), level=gt(LEVEL.CRIT))#level=in_list(LEVEL.CRIT, LEVEL.WARN))
def on_event(event) :
    notify(event, user="mdevaev", wait=2)
    notify(event, user="andozer", wait=2)
    notify(event, user="nbryskin")

