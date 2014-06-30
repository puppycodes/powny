from rules import *
@match_event(host=cmp.regexp(r"foo\d+"), status=cmp.in_list(["CRIT", "WARN"]))
def on_event(event) :
    email.send_event(("mdevaev@yandex-team.ru", "nbryskin@yandex-team.ru"), event)
    sms.send_event(("mdevaev", "nbryskin"), event)

