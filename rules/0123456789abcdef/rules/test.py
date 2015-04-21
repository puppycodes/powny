import urllib.request

from powny.core import (
    expose,
    save_job_state,
    get_cas_storage,
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


@expose
def failed_once(url):
    save_job_state()
    do_fail = get_cas_storage().replace_value(
        path="failed_once_value",
        value=False,
        default=True,
    )[0].value
    if do_fail:
        raise RuntimeError("A-HA-HA ANARCHY!!!111")
    save_job_state()
    urllib.request.build_opener().open(url)
    return "OK"
