import pytest

from powny.testing.context import run_in_context
from powny.testing.application import configured
from powny.helpers import email


# ====
def test_not_configured():
    with configured():
        with pytest.raises(RuntimeError):
            email.send_email("root@localhost", "Test", "Message")


def test_html(smtpserver):
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                server: {server}
                port: {port}
    """.format(server=smtpserver.addr[0], port=smtpserver.addr[1])):
        assert run_in_context(
            method=email.send_email,
            kwargs={
                "to":      "root@localhost",
                "subject": "Test",
                "body":    "<h4>TEST</h4>",
            },
        ).end.retval is True
    assert len(smtpserver.outbox) == 1


def test_anon_with_cc(smtpserver):
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                server: {server}
                port: {port}
    """.format(server=smtpserver.addr[0], port=smtpserver.addr[1])):
        assert run_in_context(
            method=email.send_email,
            kwargs={
                "to":      "root@localhost",
                "subject": "Test",
                "body":    "Message",
                "cc":      "cjohnson@aperturescience.com",
            },
        ).end.retval is True
    assert len(smtpserver.outbox) == 1


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
        with pytest.raises(RuntimeError):
            assert run_in_context(
                method=email.send_email,
                kwargs={
                    "to":      "root@localhost",
                    "subject": "Test",
                    "body":    "Message",
                    "fatal":   True,
                },
                fatal=True,
            ).end.retval is True
    assert len(smtpserver.outbox) == 0


def test_noop():
    with configured("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                noop: true
    """):
        assert run_in_context(
            method=email.send_email,
            kwargs={
                "to":      "root@localhost",
                "subject": "Test",
                "body":    "Message",
            },
        ).end.retval is True
