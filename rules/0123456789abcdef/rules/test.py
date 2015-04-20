import urllib.request

from powny.core import (
    expose,
    save_job_state,
)


# =====
@expose
def empty_method(**event):
    pass


@expose
def do_urlopen(url, **_):
    for _ in range(3):
        urllib.request.build_opener().open(url)
        save_job_state()
