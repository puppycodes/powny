@match_extra(user="andozer")
def on_notify(event, user) :
    user.send_email(event)
