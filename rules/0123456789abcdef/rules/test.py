import time

import powny.core
from powny.helpers import cmp
from powny.helpers import email


# =====
@powny.core.expose
def empty_method(**event):
    pass

@powny.core.expose
@powny.core.on_event
def empty_handler(**event):
    pass


# =====
@powny.core.expose
def send_email_by_event(repeat, sleep, **_):
    for count in range(repeat):
        email.send_email("root@localhost", str(count), "Test")
        time.sleep(sleep)

@powny.core.expose
@powny.core.on_event
@powny.core.match_event(cmp.equal("test", "send_email_by_event"))
def send_email_by_event_handler(**event):
    send_email_by_event(**event)
