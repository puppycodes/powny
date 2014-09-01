import smtplib
import email.mime.multipart
import email.mime.text
import email.header
import email.utils
import contextlib

from contextlog import get_logger

from ulib import validators
import ulib.validators.common  # pylint: disable=W0611
import ulib.validators.network

from powny.core.optconf import Option
from powny.core.optconf import SecretOption
from powny.core import get_config
from powny.core import get_context


# =====
def get_options():
    return {
        "email": {
            "noop": Option(
                default=False, validator=validators.common.valid_bool,
                help="Noop emails (log only)",
            ),
            "server": Option(
                default="localhost", validator=(lambda arg: validators.network.valid_ip_or_host(arg)[0]),
                help="SMTP-server hostname or IP (without port)",
            ),
            "port": Option(
                default=0, validator=validators.network.valid_port,
                help="SMTP/SMTP-SSL port",
            ),
            "ssl": Option(
                default=False, validator=validators.common.valid_bool,
                help="Use SSL connection to SMTP",
            ),
            "timeout": Option(
                default=10, validator=(lambda arg: validators.common.valid_number(arg, 0)),
                help="Socket timeout for connection",
            ),
            "user": Option(
                default=None, validator=validators.common.valid_empty,
                help="Username, none for anonymous",
            ),
            "passwd": SecretOption(
                default="", validator=str,
                help="Password",
            ),
            "from": Option(
                default="root@localhost", validator=str,
                help="Sender of the email",
            ),
            "cc": Option(
                default=[], validator=validators.common.valid_string_list,
                help="To always forward all emails",
            ),
        },
    }


# ====
def send_email(to, subject, body, cc=(), headers=None, fatal=False):
    config = get_config(check_helpers=(__name__,)).helpers.email

    to = validators.common.valid_string_list(to)
    cc = list(set(validators.common.valid_string_list(cc) + config.cc))

    message = email.mime.multipart.MIMEMultipart()
    message["From"] = config["from"]
    message["To"] = ", ".join(to)
    if len(cc) > 0:
        message["CC"] = ", ".join(cc)
    message["Date"] = email.utils.formatdate(localtime=True)
    message["Subject"] = subject
    message.attach(email.mime.text.MIMEText(body))

    email_headers = {"Powny-Job-Id": get_context().get_job_id()}
    email_headers.update(headers or {})
    for name in email_headers:
        message[name] = email.header.Header(header_name=name, s=email_headers[name])

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
    get_context().save()
    return ok
