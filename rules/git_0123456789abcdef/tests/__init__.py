import urllib.request
import json

from raava import rules

def echo_event(event, *args):
    if isinstance(event, rules.EventRoot):
        event = dict(event) # Dropping extra fields
    opener = urllib.request.build_opener()
    request = urllib.request.Request(
        "http://%(echo_host)s:%(echo_port)d" % (event),
        data=json.dumps((event,) + args).encode(),
    )
    opener.open(request)

