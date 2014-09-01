import uuid

import pytest

from powny.core import context


# =====
class _FakeContext:
    def save(self):
        pass

    def get_job_id(self):
        return str(uuid.uuid4())


@pytest.yield_fixture
def fake_context():
    context._fake_context = _FakeContext()  # pylint: disable=W0212
    try:
        yield
    finally:
        context._fake_context = None  # pylint: disable=W0212
