####
# Вариант первый: откладываем все ночные события до утра, способ доставки событий описывают юзеры
####
@match_event(host="foo", service="bar") :
def on_event(event) :
    if not (time("9:00") <= event.time_start <= time("21:00")) :
        wait_until("9:00")
    notify(event, user="andozer", wait=10)
    notify(event, user="disarmer", wait=10)
    get_maillist("monitor-admins@yandex-team.ru").send_email(event)


####
# Способ второй: откладывание реализует пользователь сам для себя, он же описывает собственную логику оповещений
####
@match_urgency(URGENCY.HIGH, URGENCY.MEDIUM)
def on_notify(event) :
    if not (time("9:00") <= event.time_start <= time("21:00")) :
        wait_until("9:00")
    if event.user.is_buisness_time() :
        event.user.send_email(event)
        event.user.send_sms(event)
    else :
        event.user.call_via_duty(event, wait=2)
        event.user.call_via_duty(event, wait=2)
    wait("2m")
    get_user("asimakov").send(event, METHOD.EMAIL)

@match_urgency(URGENCY.LOW)
def on_notify(event) :
    if not (time("9:00") <= event.time_start <= time("21:00")) :
        delay_until("9:00")
    if event.user.is_buisness_time() :
        if event.level == LEVEL.CRIT :
            event.user.send_email(event)
            event.user.send_sms(event)
        else :
            event.user.send_email(event)

