from rules import *
def on_event(event):
    email.send_event("mdevaev@yandex-team.ru", event)
    email.send_event("nbryskin@yandex-team.ru", event)

