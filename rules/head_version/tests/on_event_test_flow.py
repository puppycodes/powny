import urllib.request
import json
import time

@match_event(host="test_flow")
def on_event(event):
    opener = urllib.request.build_opener()
    request = urllib.request.Request(
        "http://localhost:7888",
        data=json.dumps(dict(event)).encode(),
    )
    time.sleep(5)
    opener.open(request)

