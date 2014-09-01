# pylint: disable=R0904
# pylint: disable=W0212


import pytest
import vcr

from powny.helpers import hipchat

from .fixtures.application import configured
from .fixtures.context import fake_context  # pylint: disable=W0611


# ====
def test_not_configured():
    with configured():
        with pytest.raises(RuntimeError):
            hipchat.send_to_room("robots", "Test")


@pytest.mark.usefixtures("fake_context")
def test_no_token():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
    """):
        with pytest.raises(RuntimeError):
            hipchat.send_to_room("robots", "Test", fatal=True)


@vcr.use_cassette("tests/fixtures/vcr/helpers_hipchat_test_ok.yaml")
@pytest.mark.usefixtures("fake_context")
def test_ok():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
            hipchat:
                token: FAKE_TOKEN
    """):
        assert hipchat.send_to_room("robots", "Test", fatal=True) is True


@pytest.mark.usefixtures("fake_context")
def test_noop():
    with configured("""
        helpers:
            configure:
                - powny.helpers.hipchat
            hipchat:
                noop: true
    """):
        assert hipchat.send_to_room("robots", "Test") is True
