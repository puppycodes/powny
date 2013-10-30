##### Пользовательские оповещения #####
@match_urgency(URGENCY.HIGH, URGENCY.MEDIUM)
def notify(me, event) :
    if me.is_buisness_time() :
        me.send(event, METHOD.EMAIL)
        me.send(event, METHOD.SMS)
    else :
        me.send(event, METHOD.CALL)
        wait(2)
        me.send(event, METHOD.CALL)
    wait(2)
    get_user("asimakov").send(event, METHOD.EMAIL)

@match_urgency(URGENCY.LOW)
def notify(me, event) :
    if me.is_buisness_time() :
        if event.level == LEVEL.CRIT :
            me.send(event, METHOD.EMAIL)
            me.send(event, METHOD.SMS)
        else :
            me.send(event, METHOD.EMAIL)

@match_urgency(URGENCY.CUSTOM)
def notify(me, event) :
    me.send(event, METHOD.EMAIL)

