import contextlib

import pytest

from powny.backends.zookeeper import zoo
from powny.backends.zookeeper import Backend


# =====
def _cleanup():
    with zoo.Client(chroot=None, **zclient_kwargs()).connected() as client:
        with client.make_write_request("cleanup()") as request:
            request.delete(zclient_chroot(), recursive=True)


@contextlib.contextmanager
def _make_client():
    _cleanup()
    with zoo.Client(chroot=None, **zclient_kwargs()).connected() as client:
        with client.make_write_request() as request:
            request.create(zclient_chroot())
        client = zoo.Client(chroot=zclient_chroot(), **zclient_kwargs())
        client.open()
        try:
            yield client
        finally:
            try:
                client.close()
            finally:
                _cleanup()


# =====
@pytest.fixture
def zclient_kwargs():
    return {
        "nodes": ("localhost:2181",),
        "timeout": 5,
        "start_timeout": 10,
        "start_retries": 5,
        "randomize_hosts": True,
    }


@pytest.fixture
def zclient_chroot():
    return "/powny-tests"


@pytest.yield_fixture
def zclient():
    with _make_client() as client:
        yield client


@pytest.fixture
def zbackend_kwargs():
    kwargs = dict(zclient_kwargs())
    kwargs["chroot"] = zclient_chroot()
    return kwargs


@pytest.yield_fixture
def zbackend():
    with _make_client():
        with Backend(**zbackend_kwargs()).connected() as backend:
            yield backend
