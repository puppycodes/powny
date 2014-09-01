# pylint: disable=R0904
# pylint: disable=W0212


import smtplib

import pytest

from powny.helpers import email

from .fixtures.application import configured
from .fixtures.context import fake_context  # pylint: disable=W0611


# ====
def test_not_configured():
    with configured():
        with pytest.raises(RuntimeError):
            email.send_email("root@localhost", "Test", "Message")


@pytest.mark.usefixtures("fake_context")
def test_anon_with_cc(smtpserver):
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                server: {server}
                port: {port}
    """.format(server=smtpserver.addr[0], port=smtpserver.addr[1])):
        assert email.send_email("root@localhost", "Test", "Message", cc="cjohnson@aperturescience.com") is True
    assert len(smtpserver.outbox) == 1


@pytest.mark.usefixtures("fake_context")
def test_with_login(smtpserver):
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                server: {server}
                port: {port}
                user: foo
                passwd: bar
    """.format(server=smtpserver.addr[0], port=smtpserver.addr[1])):
        with pytest.raises(smtplib.SMTPException):
            email.send_email("root@localhost", "Test", "Message", fatal=True)
    assert len(smtpserver.outbox) == 0


@pytest.mark.usefixtures("fake_context")
def test_noop():
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                noop: true
    """):
        assert email.send_email("root@localhost", "Test", "Message") is True
