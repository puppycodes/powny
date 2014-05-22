import multiprocessing
import threading
import http.server
import urllib.request
import json
import unittest
import time
import logging

import gns.reinit
import gns.api
import gns.splitter
import gns.worker
import gns.collector
import gns.service


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public classes #####
class TestFlow(unittest.TestCase): # pylint: disable=R0904
    _echo_attrs = {
        "echo_host": "localhost",
        "echo_port": 7888,
    }

    @classmethod
    def setUpClass(cls):
        config = gns.service.load_config(config_file_path="etc/gns-test.d/gns.yaml")
        gns.service.init_logging(config)
        proc = multiprocessing.Process(target=gns.reinit.run, args=(config,))
        proc.start()
        proc.join()
        cls._services = [
            threading.Thread(target=method, args=(config,))
            for method in (
                gns.api.run,
                gns.splitter.run,
                gns.worker.run,
                gns.collector.run,
            )
        ]
        for service in cls._services:
            service.daemon = True
            service.start()
        time.sleep(3) # wait for services to start and initialize


    ### Tests ###

    def test_flow_ends_urlopen(self):
        _logger.debug("----- BEGIN: test_flow_ends_urlopen() -----")
        event = {
            "host":    "test_flow",
            "service": "foo",
            "custom":  123,
        }
        event.update(self._echo_attrs)
        self.assertEqual(_send_recv_event(event), [event])
        _logger.debug("----- END: test_flow_ends_urlopen() -----")

    def test_flow_previous_state(self):
        _logger.debug("----- BEGIN: test_flow_previous_state() -----")
        events = []
        for count in range(6):
            event = {
                "host":   "test_state",
                "custom": count,
            }
            event.update(self._echo_attrs)
            events.append(event)
        for (count, (current, previous)) in enumerate(zip(events, [None] + events)):
            _logger.debug("----- STEP %d: test_flow_previous_state() -----", count)
            self.assertEqual(_send_recv_event(current), [current, previous])
        _logger.debug("----- END: test_flow_previous_state() -----")


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
    try:
        # To save events had not numbered sequentially. Check that everything works to increase counter.
        opener.open(_make_event_request({ "_stub": None }))
        opener.open(_make_event_request(event))
        return json.loads(server.wait_for_result().decode())
    finally:
        server.stop()


##### Private classes #####
class _ShotServer(http.server.HTTPServer, threading.Thread):
    def __init__(self, host_name, port):
        http.server.HTTPServer.__init__(self, (host_name, port), _ShotHandler)
        threading.Thread.__init__(self)
        self._result = None
        self._finished = threading.Condition()

    def wait_for_result(self):
        with self._finished:
            while self._result is None:
                _logger.debug("waiting for result")
                self._finished.wait()
            return self._result

    def put_result(self, result):
        assert result is not None, "result should not be None"
        with self._finished:
            self._result = result
            _logger.debug("the result obtained")
            self._finished.notify()

    def stop(self):
        _logger.debug("stopping one-shot server %s", self)
        self.shutdown()
        self.server_close()
        self.join()

    def run(self):
        _logger.debug("starting one-shot server %s", self)
        self.serve_forever()

class _ShotHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        result = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")
        _logger.debug("shot-server got the result")
        self.server.put_result(result)
        _logger.debug("shot-server put the result")

    def log_message(self, format, *args): # pylint: disable=W0622
        _logger.info("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % (args))

