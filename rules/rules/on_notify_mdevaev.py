@match_extra(user="mdevaev")
def on_notify(event):
    send(event, method=METHOD.EMAIL, wait=5)
    send(event, method=METHOD.EMAIL)

