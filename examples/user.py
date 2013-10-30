##### Пользовательские оповещения #####
@match_urgency(URGENCY.HIGH, URGENCY.MEDIUM)
def notify(me, event) :
    if me.is_buisness_time() :
        me.send_email(event)
        me.send_sms(event)
    else :
        me.call_via_duty(event)
        wait(2)
        me.call_via_duty(event)
    wait(2)
    get_user("asimakov").send(event, METHOD.EMAIL)

@match_urgency(URGENCY.LOW)
def notify(me, event) :
    if me.is_buisness_time() :
        if event.level == LEVEL.CRIT :
            me.send_email(event)
            me.send_sms(event)
        else :
            me.send_email(event)

@match_urgency(URGENCY.CUSTOM)
def notify(me, event) :
    me.send_email(event)

