import os
import subprocess
import http.server
import urllib.request
import json
import unittest
import time


##### Public classes #####
class TestFlow(unittest.TestCase):
    def setUp(self):
        env = dict(os.environ)
        env.update({ "LC_ALL": "C", "PYTHONPATH": "." })
        subprocess.check_output(("python3", "scripts/gns-reinit.py", "--do-it-now"), env=env)
        self._services = [
            subprocess.Popen(cmd, env=env)
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
        request = urllib.request.Request(
            "http://localhost:7887/api/rest/v1/jobs",
            data=json.dumps(event).encode(),
            headers={ "Content-Type": "application/json" })
        opener = urllib.request.build_opener()
        opener.open(request)
        self.assertEqual(json.loads(self._get_post().decode()), event)


    ### Private ###

    def _get_post(self):
        class shot_handler(http.server.BaseHTTPRequestHandler):
            result = None
            def do_POST(self):
                shot_handler.result = self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
        server = http.server.HTTPServer(("localhost", 7888), shot_handler)
        server.handle_request()
        return shot_handler.result

