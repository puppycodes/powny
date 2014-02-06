@match_event(host=regexp(r"foo\d+"), status=in_list(STATUS.CRIT, STATUS.WARN))
def on_event(event) :
    email.send(("mdevaev@yandex-team.ru", "nbryskin@yandex-team.ru"), event)
    sms.send(("mdevaev", "nbryskin"), event)

