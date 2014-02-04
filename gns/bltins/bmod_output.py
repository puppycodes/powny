import urllib.request
import urllib.parse
import urllib.error

import smtplib
import email.mime.multipart
import email.mime.text
import email.utils

import pprint
import time
import logging

from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.network

from raava import worker

from . import bmod_const
from .. import gnsint


##### Public constants #####
S_OUTPUT = "output"
S_SMS    = "sms"
S_EMAIL  = "email"

O_NOOP     = "noop"
O_SEND_URL = "send-url"
O_SERVER   = "server"
O_USER     = "user"
O_PASSWD   = "passwd"
O_FROM     = "from"
O_CC       = "cc"


###
CONFIG_MAP = {
    S_OUTPUT: {
        O_NOOP: (False, validators.common.valid_bool),

        S_SMS: {
            O_SEND_URL: ("http://example.com", str),
        },

        S_EMAIL: {
            O_SERVER: ("localhost",      lambda arg: validators.network.valid_ip_or_host(arg)[0]),
            O_USER:   ("root",           str),
            O_PASSWD: ("passwd",         str),
            O_FROM:   ("root@localhost", str),
            O_CC:     ([],               validators.common.valid_string_list),
        },
    },
}


##### Private objects #####
_logger = logging.getLogger("output")


##### Private methods #####
def _send_sms(task, event_root, to_list):
    if not isinstance(to_list, (list, tuple)):
        to_list = [str(to_list)]

    message = "%s %s:%s = %s" % (
        time.strftime("%H:%M.%S %d-%m-%Y"),
        event_root.get(bmod_const.EVENT.HOST),
        event_root.get(bmod_const.EVENT.SERVICE),
        event_root.get(bmod_const.EVENT.STATUS),
    )

    request = urllib.request.Request(
        gnsint.get_config(S_OUTPUT, S_SMS, O_SEND_URL),
        data=urllib.parse.urlencode({
                "resps": ",".join(to_list),
                "msg":   message,
            }).encode(),
        )
    opener = urllib.request.build_opener()
    _logger.debug("Sending to Golem SMS API: %s", to_list)

    task.checkpoint()

    if not gnsint.get_config(S_OUTPUT, O_NOOP):
        try:
            result = opener.open(request).read().decode().strip()
            _logger.info("SMS sent to Golem to %s, response: %s", to_list, result)
        except urllib.error.HTTPError as err:
            result = err.read().decode().strip()
            _logger.exception("Failed to send SMS to %s, response: %s", to_list, result)
    else:
        _logger.info("SMS sent to Golem (noop) to %s", to_list)

    task.checkpoint()

def _send_email(task, event_root, to_list):
    if not isinstance(to_list, (list, tuple)):
        to_list = [str(to_list)]

    subject = "GNS message: %s:%s = %s" % (
        event_root.get(bmod_const.EVENT.HOST),
        event_root.get(bmod_const.EVENT.SERVICE),
        event_root.get(bmod_const.EVENT.STATUS),
    )
    text = "Event extra:\n\n%s\n\nEvent dump:\n\n%s" % (pprint.pformat(event_root.get_extra()), pprint.pformat(event_root))

    send_from = gnsint.get_config(S_OUTPUT, S_EMAIL, O_FROM)
    cc_list = gnsint.get_config(S_OUTPUT, S_EMAIL, O_CC)

    message = email.mime.multipart.MIMEMultipart()
    message["From"] = send_from
    message["To"] = ", ".join(to_list)
    if len(cc_list) != 0:
        message["CC"] = ", ".join(cc_list)
    message["Date"] = email.utils.formatdate(localtime=True)
    message["Subject"] = subject
    message.attach(email.mime.text.MIMEText(text))

    server_host = gnsint.get_config(S_OUTPUT, S_EMAIL, O_SERVER)
    user = gnsint.get_config(S_OUTPUT, S_EMAIL, O_USER)
    passwd = gnsint.get_config(S_OUTPUT, S_EMAIL, O_PASSWD)

    _logger.debug("Sending email to: %s; cc: %s; via SMTP/SSL %s@%s", to_list, cc_list, user, server_host)

    task.checkpoint()

    if not gnsint.get_config(S_OUTPUT, O_NOOP):
        server = smtplib.SMTP_SSL(server_host)
        try:
            server.login(user, passwd)
            server.sendmail(send_from, to_list + cc_list, message.as_string())
            _logger.info("Email sent to: %s; cc: %s", to_list, cc_list)
        except Exception:
            _logger.exception("Failed to send email to: %s; cc: %s", to_list, cc_list)
        finally:
            server.close()
    else:
        _logger.info("Email sent to: %s; cc: %s (noop)", to_list, cc_list)

    task.checkpoint()


##### Public constants #####
BUILTINS_MAP = {
    "send_sms":   worker.make_task_builtin(_send_sms),
    "send_email": worker.make_task_builtin(_send_email),
}

