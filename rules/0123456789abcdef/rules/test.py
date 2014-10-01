import urllib.request

from powny.core import (
    expose,
    on_event,
    match_event,
    save_job_state,
)


# =====
@expose
def empty_method(**event):
    pass


@expose
@on_event
def empty_handler(**event):
    pass


# =====
@expose
def do_urlopen(url, **_):
    for _ in range(3):
        urllib.request.build_opener().open(url)
        save_job_state()


@expose
@on_event
@match_event(lambda event: event["test"] == "urlopen_by_event")
def urlopen_by_event(**event):
    do_urlopen(**event)
