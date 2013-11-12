@match_extra(user="mdevaev")
@match_event(level=LEVEL.CRIT)
def on_notify(event, user) :
    user.send_email(event, wait=2)
    user.send_sms(event, wait=2)
