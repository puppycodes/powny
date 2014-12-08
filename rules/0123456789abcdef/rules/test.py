import urllib.request

from powny.core import (
    expose,
    save_job_state,
)

from powny.core.golem import (
    on_event,
    match_event,
)


# =====
@expose
def empty_method(**event):
    pass


@expose
@on_event
def empty_handler(previous, current):
    pass


# =====
@expose
def do_urlopen(url, **_):
    for _ in range(3):
        urllib.request.build_opener().open(url)
        save_job_state()


@expose
@on_event
@match_event(lambda _, current: current.service == "urlopen_by_event")
def urlopen_by_event(previous, current):
    do_urlopen(current.description)
    return ((previous and previous.get_raw()), current.get_raw())
