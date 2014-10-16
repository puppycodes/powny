import time

from powny.core import tools


# =====
def test_iso8601_funcs():
    now = int(time.time())
    assert tools.from_isotime(tools.make_isotime(now)) == now
