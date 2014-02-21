@match_event(host=cmp.regexp(r"foo\d+"), status=cmp.in_list(["CRIT", "WARN"]))
def on_event(event) :
    email.send(("mdevaev@yandex-team.ru", "nbryskin@yandex-team.ru"), event)
    sms.send(("mdevaev", "nbryskin"), event)

