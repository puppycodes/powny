import urllib.request
import json

from raava import rules

def echo_event(event):
    if isinstance(event, rules.EventRoot):
        event = dict(event) # Dropping extra fields
    opener = urllib.request.build_opener()
    request = urllib.request.Request(
        "http://localhost:7888",
        data=json.dumps(event).encode(),
    )
    opener.open(request)

