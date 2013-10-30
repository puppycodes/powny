##### Перехват нотификаций одних пользователей другим #####
@match_event(user=("andozer", "disarmer"), method=METHOD.CALL)
def on_send(event) : # Тут еще прилетят event.user и event.method
    get_user("asimakov").send_email(event)

