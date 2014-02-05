@match_event(host=regexp(r"foo\d+"), status=in_list(STATUS.CRIT, STATUS.WARN))
def on_event(event) :
    send_email(("mdevaev@yandex-team.ru", "nbryskin@yandex-team.ru"), event)
    send_sms(("mdevaev", "nbryskin"), event)

