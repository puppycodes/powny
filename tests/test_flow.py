import os
import subprocess
import threading
import http.server
import urllib.request
import json
import unittest
import time
import logging


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public classes #####
class TestFlow(unittest.TestCase): # pylint: disable=R0904
    _echo_attrs = {
        "echo_host": "localhost",
        "echo_port": 7888,
    }

    def setUp(self):
        env = dict(os.environ)
        env.update({ "LC_ALL": "C", "PYTHONPATH": "." })
        conf_opt = ("-c", "etc/gns-test.d")
        subprocess.check_output(("python3", "scripts/gns-reinit.py", "--do-it-now") + conf_opt, env=env)
        self._services = [
            subprocess.Popen(cmd + conf_opt, env=env)
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
        event.update(self._echo_attrs)
        self.assertEqual(_send_recv_event(event), [event])

    def test_flow_previous_state(self):
        events = []
        for count in range(6):
            event = {
                "host":   "test_state",
                "custom": count,
            }
            event.update(self._echo_attrs)
            events.append(event)
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
    opener = urllib.request.build_opener()
    server = _ShotServer(event["echo_host"], event["echo_port"])
    server.start()
    time.sleep(1)
    # To save events had not numbered sequentially. Check that everything works to increase counter.
    opener.open(_make_event_request({ "_stub": None }))
    time.sleep(1)
    opener.open(_make_event_request(event))
    time.sleep(1)
    return json.loads(server.get_result().decode())


##### Private classes #####
class _ShotServer(http.server.HTTPServer, threading.Thread):
    def __init__(self, host_name, port):
        http.server.HTTPServer.__init__(self, (host_name, port), _ShotHandler)
        threading.Thread.__init__(self)

    def run(self):
        self.handle_request()
        self.server_close()

    def get_result(self):
        assert hasattr(self, "result"), "No result readed"
        return self.result # pylint: disable=E1101

class _ShotHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.result = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args): # pylint: disable=W0622
        _logger.debug("%s - - [%s] %s", self.address_string(), self.log_date_time_string, format % (args))

