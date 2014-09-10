import smtplib
import email.mime.multipart
import email.mime.text
import email.header
import email.utils
import contextlib

from contextlog import get_logger

from ulib.validators.common import (
    valid_number,
    valid_bool,
    valid_empty,
    valid_string_list,
)
from ulib.validators.network import (
    valid_ip_or_host,
    valid_port,
)

from powny.core.optconf import (
    Option,
    SecretOption,
)
from powny.core import (
    get_config,
    get_job_id,
    save_job_state,
)


# =====
def get_options():
    return {
        "email": {
            "noop": Option(
                default=False, type=valid_bool,
                help="Noop emails (log only)",
            ),
            "server": Option(
                default="localhost", type=(lambda arg: valid_ip_or_host(arg)[0]),
                help="SMTP-server hostname or IP (without port)",
            ),
            "port": Option(
                default=0, type=valid_port,
                help="SMTP/SMTP-SSL port",
            ),
            "ssl": Option(
                default=False, type=valid_bool,
                help="Use SSL connection to SMTP",
            ),
            "timeout": Option(
                default=10, type=(lambda arg: valid_number(arg, 0)),
                help="Socket timeout for connection",
            ),
            "user": Option(
                default=None, type=valid_empty,
                help="Username, none for anonymous",
            ),
            "passwd": SecretOption(
                default="", type=str,
                help="Password",
            ),
            "from": Option(
                default="root@localhost", type=str,
                help="Sender of the email",
            ),
            "cc": Option(
                default=[], type=valid_string_list,
                help="To always forward all emails",
            ),
        },
    }


# ====
def send_email(to, subject, body, html=False, cc=(), headers=None, fatal=False):
    config = get_config(check_helpers=(__name__,)).helpers.email
    to = valid_string_list(to)
    cc = list(set(valid_string_list(cc) + config.cc))

    message = _make_message(config["from"], to, subject, body, html, cc, headers)

    logger = get_logger()

    ok = False
    noop = ("[NOOP] " if config.noop else "")
    logger.info("%sSending email to: %s; cc: %s; subject: %s", noop, to, cc, subject)
    logger.debug("Email content:\n%s", message.as_string())

    if not config.noop:
        smtp_class = (smtplib.SMTP_SSL if config.ssl else smtplib.SMTP)
        try:
            with contextlib.closing(smtp_class(config.server, config.port, timeout=config.timeout)) as client:
                if config.user is not None:
                    client.login(config.user, config.passwd)
                client.sendmail(config["from"], to + cc, message.as_string())
                ok = True
        except Exception:
            logger.exception("%sFailed to send email to: %s; cc: %s; subject: %s", noop, to, cc, subject)
            if fatal:
                raise
    else:
        ok = True
    if ok:
        logger.info("%sEmail sent to: %s; cc: %s; subject: %s", noop, to, cc, subject)

    del logger
    save_job_state()
    return ok


def _make_message(sender, to, subject, body, html=False, cc=(), headers=None):
    message = email.mime.multipart.MIMEMultipart()

    message["From"] = sender
    message["To"] = ", ".join(to)
    if len(cc) > 0:
        message["CC"] = ", ".join(cc)
    message["Date"] = email.utils.formatdate(localtime=True)
    message["Subject"] = subject
    message.attach(email.mime.text.MIMEText(body, ("html" if html else "plain")))

    email_headers = {"Powny-Job-Id": get_job_id()}
    email_headers.update(headers or {})
    for name in email_headers:
        message[name] = email.header.Header(header_name=name, s=email_headers[name])

    return message
