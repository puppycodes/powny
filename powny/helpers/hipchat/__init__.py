import json

import requests

from contextlog import get_logger

from ulib.validators.common import (
    valid_number,
    valid_bool,
    valid_empty,
    valid_range,
)

from powny.core.optconf import (
    Option,
    SecretOption,
)
from powny.core import (
    get_config,
    save_job_state,
)


# =====
def get_options():
    return {
        "hipchat": {
            "noop": Option(
                default=False, type=valid_bool,
                help="Noop HipChat messages (log only)",
            ),
            "url": Option(
                default="https://api.hipchat.com/v1", type=str,
                help="HipChat API URL",
            ),
            "timeout": Option(
                default=10, type=(lambda arg: valid_number(arg, 0)),
                help="Socket timeout for connection",
            ),
            "token": SecretOption(
                default=None, type=valid_empty,
                help="Default auth token (see https://www.hipchat.com/docs/api/auth)",
            ),
            "sender": Option(
                default="Switty Bot", type=str,
                help="Default sender name",
            ),
            "color": Option(
                default="purple", type=(lambda arg: valid_range(arg, _COLORS)),
                help="Default message color (see https://www.hipchat.com/docs/api/method/rooms/message)",
            ),
        },
    }


# ====
_COLORS = ("yellow", "red", "green", "purple", "gray", "random")


def send_to_room(to, body, sender=None, color=None, notify=False, token=None, fatal=False):
    config = get_config(check_helpers=(__name__,)).helpers.hipchat
    logger = get_logger()

    ok = False
    noop = ("[NOOP] " if config.noop else "")
    logger.info("%sSending HipChat message to room: %s; message: %s", noop, to, body)

    color = valid_range((color or config.color), _COLORS)

    if not config.noop:
        try:
            # https://www.hipchat.com/docs/api/method/rooms/message
            token = (token or config.token)
            if not token:
                raise RuntimeError("Helper '{}' requires the HipChat token".format(__name__))
            requests.post(config.url + "/rooms/message", data={
                "room_id":        to,
                "from":           (sender or config.sender)[:15],
                "message":        body,
                "message_format": "text",
                "color":          color,
                "notify":         int(notify),
            }, params={
                "auth_token": token,
            }, timeout=config.timeout).raise_for_status()
            ok = True
        except Exception:
            logger.exception("%sFailed to send HipChat message to room: %s", noop, to)
            if fatal:
                raise
    else:
        ok = True
    if ok:
        logger.info("%sHipChat message sent to room: %s", noop, to)

    del logger
    save_job_state()
    return ok
