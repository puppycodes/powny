import urllib.request
import json

def echo_event(event):
    opener = urllib.request.build_opener()
    request = urllib.request.Request(
        "http://localhost:7888",
        data=json.dumps(dict(event)).encode(),
    )
    opener.open(request)

