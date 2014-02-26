import os
import subprocess
import threading
import http.server
import urllib.request
import json
import unittest
import time


##### Public classes #####
class TestFlow(unittest.TestCase): # pylint: disable=R0904
    def setUp(self):
        env = dict(os.environ)
        env.update({ "LC_ALL": "C", "PYTHONPATH": "." })
        subprocess.check_output(("python3", "scripts/gns-reinit.py", "--do-it-now", "--quiet"), env=env)
        self._services = [
            subprocess.Popen(cmd + ("--quiet",), env=env)
            for cmd in (
                ("python3", "scripts/gns-api.py"),
                ("pypy3",   "scripts/gns-splitter.py"),
                ("pypy3",   "scripts/gns-worker.py"),
                ("pypy3",   "scripts/gns-collector.py"),
            )
        ]
        time.sleep(3)

    def tearDown(self):
        for service in self._services:
            service.kill()


    ### Tests ###

    def test_flow_ends_urlopen(self):
        event = {
            "host":    "test_flow",
            "service": "foo",
            "custom":  123,
        }
        self.assertEqual(_send_recv_event(event), event)

    def test_flow_previous_state(self):
        events = [
            {
                "host":   "test_state",
                "custom": count,
            } for count in range(6)
        ]
        for (current, previous) in zip(events, [None] + events):
            self.assertEqual(_send_recv_event(current), [current, previous])


##### Private methods #####
def _make_event_request(event):
    return urllib.request.Request(
        "http://localhost:7887/api/rest/v1/jobs",
        data=json.dumps(event).encode(),
        headers={ "Content-Type": "application/json" },
    )

def _send_recv_event(event):
    # To save events had not numbered sequentially. Check that everything works to increase counter.
    stub = _make_event_request({ "_stub": None })

    request = _make_event_request(event)
    opener = urllib.request.build_opener()
    server = _ShotServer("localhost", 7888)
    server.start()
    time.sleep(4)
    try:
        opener.open(stub)
        time.sleep(1)
        opener.open(request)
    finally:
        server.stop()
    time.sleep(1)
    return json.loads(server.get_result().decode())


##### Private classes #####
class _ShotServer(threading.Thread):
    def __init__(self, host_name, port):
        threading.Thread.__init__(self)
        self._server = http.server.HTTPServer((host_name, port), _ShotHandler)

    def run(self):
        self._server.serve_forever()

    def stop(self):
        self._server.shutdown()
        self._server.socket.close()

    def get_result(self):
        assert hasattr(self._server, "result"), "No result readed"
        return self._server.result # pylint: disable=E1101

class _ShotHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.result = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

