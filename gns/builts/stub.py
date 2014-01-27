import time
import logging


##### Private objects #####
_logger = logging.getLogger("outgoing")


##### Stubs #####
def builtin_notify(task, event_root, user, wait = 0):
    task.checkpoint()
    event_root = event_root.copy()
    event_root.get_extra()[EXTRA.USER] = user
    task.fork(event_root, HANDLER.ON_NOTIFY)
    _logger.info("\x1b[31;1mNOTIFY: user=%s, sleep=%d\x1b[0m" % (user, wait))
    task.checkpoint()
    time.sleep(wait)
    task.checkpoint()

def _send_stub(task, event_root, method, wait = 0):
    task.checkpoint()
    event_root = event_root.copy()
    event_root.get_extra()[EXTRA.METHOD] = method
    task.fork(event_root, HANDLER.ON_SEND)
    _logger.info("\x1b[31;1mSEND: user=%s, method=%s, sleep=%d\x1b[0m" % (event_root.get_extra()[EXTRA.USER], method, wait))
    task.checkpoint()
    time.sleep(wait)
    task.checkpoint()

builtin_send = _send_stub

def builtin_send_email(task, event_root, wait = 0):
    _send_stub(task, event_root, METHOD.EMAIL, wait = 0)

def builtin_send_sms(task, event_root, wait = 0):
    _send_stub(task, event_root, METHOD.SMS, wait = 0)

