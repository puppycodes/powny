##### Правило по хосту в группе и сервису #####
@match_event(host=GROUPS.CONDUCTOR("mgolem-api"), service="Golem", level=LEVEL.CRIT)
def on_event(event) : # В обработчик прилетает копия объекта
    while event.time_start + 1800 > now() :
        notify(event, user="andozer", wait=10) # URGENCY.MEDIUM
        notify(event, user="disarmer", wait=10)
    while event.time_start + 3600 > now() :
        notify(event, login="andozer", urgency=URGENCY.HIGH, wait=10)
        notify(event, login="disarmer", urgency=URGENCY.HIGH, wait=10)

    event.text = "В течении полутора часов, andozer и disarmer не ответили на сообщение\n-----\n" + event.text
    get_maillist("monitor-admins@yandex-team.ru").send(event)


##### Правило, имитирующее список ответственных #####
@match_event(host="foo", service="bar")
def on_event(event) :
    urgency = {
        LEVEL.CRIT : URGENCY.HIGH,
        LEVEL.WARN : URGENCY.MEDIUM,
    }.get(event.level, URGENCY.LOW)
    for user in ("user1", "user2", "user3", "user4", "user5") :
        notify(event, user=user, urgency=urgency, wait=5)

