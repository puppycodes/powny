import pytest
import vcr

from powny.helpers import hipchat

from .fixtures.application import configured
from .fixtures.context import run_in_context


# ====
def test_not_configured():
    with configured():
        with pytest.raises(RuntimeError):
            hipchat.send_to_room("robots", "Test")


def test_no_token():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
    """):
        with pytest.raises(RuntimeError):
            run_in_context(
                method=hipchat.send_to_room,
                kwargs={
                    "to":    "robots",
                    "body":  "Test",
                    "fatal": True,
                },
            )


@vcr.use_cassette("tests/fixtures/vcr/helpers_hipchat_test_ok.yaml")
def test_ok():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
            hipchat:
                token: FAKE_TOKEN
    """):
        assert run_in_context(
            method=hipchat.send_to_room,
            kwargs={
                "to":    "robots",
                "body":  "Test",
                "fatal": True,
            },
        ).end.retval is True


@vcr.use_cassette("tests/fixtures/vcr/helpers_hipchat_test_html_ok.yaml")
def test_html_ok():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
            hipchat:
                token: FAKE_TOKEN
    """):
        assert run_in_context(
            method=hipchat.send_to_room,
            kwargs={
                "to":    "robots",
                "body":  "Test <i>test</i> <b>test</b>",
                "html":  True,
                "fatal": True,
            },
        ).end.retval is True


def test_noop():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
            hipchat:
                noop: true
    """):
        assert run_in_context(
            method=hipchat.send_to_room,
            kwargs={
                "to":    "robots",
                "body":  "Test",
            },
        ).end.retval is True
