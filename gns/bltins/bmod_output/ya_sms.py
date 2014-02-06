import urllib.request
import urllib.parse
import urllib.error

import time
import logging

from raava import worker

from . import common
from .. import bmod_const
from ... import env


##### Public constants #####
S_SMS    = "sms"
O_SEND_URL = "send-url"
O_CC       = "cc"


###
CONFIG_MAP = {
    common.S_OUTPUT: {
        S_SMS: {
            O_SEND_URL: ("http://example.com", str),
        },
    },
}


##### Private objects #####
_logger = logging.getLogger(common.LOGGER_NAME)


##### Private methods #####
def _send_sms(task, to_list, event_root):
    if not isinstance(to_list, (list, tuple)):
        to_list = [str(to_list)]

    message = "%s %s:%s = %s" % (
        time.strftime("%H:%M.%S %d-%m-%Y"),
        event_root.get(bmod_const.EVENT.HOST),
        event_root.get(bmod_const.EVENT.SERVICE),
        event_root.get(bmod_const.EVENT.STATUS),
    )

    request = urllib.request.Request(
        env.get_config(common.S_OUTPUT, S_SMS, O_SEND_URL),
        data=urllib.parse.urlencode({
                "resps": ",".join(to_list),
                "msg":   message,
            }).encode(),
        )
    opener = urllib.request.build_opener()
    _logger.debug("Sending to Golem SMS API: %s", to_list)

    task.checkpoint()

    if not env.get_config(common.S_OUTPUT, common.O_NOOP):
        try:
            result = opener.open(request).read().decode().strip()
            _logger.info("SMS sent to Golem to %s, response: %s", to_list, result)
        except urllib.error.HTTPError as err:
            result = err.read().decode().strip()
            _logger.exception("Failed to send SMS to %s, response: %s", to_list, result)
        except Exception:
            _logger.exception("Failed to send SMS to %s", to_list)
    else:
        _logger.info("SMS sent to Golem (noop) to %s", to_list)

    task.checkpoint()


##### Public constants #####
BUILTINS_MAP = {
    "send_sms": worker.make_task_builtin(_send_sms),
}

