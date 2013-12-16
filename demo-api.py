#!/usr/bin/env pypy3

import json
import wsgiref.simple_server
import cgi

from raava import zoo
from raava import rules
from raava import events

import gns.stub

def webapi(env_dict, start_response):
    path = env_dict["PATH_INFO"]
    client = zoo.connect(["localhost"])
    try:
        if path == "/add":
            data = env_dict["wsgi.input"].read(int(env_dict["CONTENT_LENGTH"]))
            event_root = rules.EventRoot(json.loads(data.decode()))
            retval = events.add(client, event_root, gns.stub.HANDLER.ON_EVENT)
        elif path == "/cancel":
            events.cancel(client, cgi.parse_qs(env_dict["QUERY_STRING"])["job_id"][0])
            retval = None
        else:
            raise Exception("Unknown method")
    except Exception as err:
        start_response("500 Internal Error", [("Content-Type", "text/plain")])
        return [("ERROR: %s" % (str(err))).encode()]
    finally:
        client.stop()
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [json.dumps({ "retval": retval }).encode()]

httpd = wsgiref.simple_server.make_server("", 8080, webapi)
httpd.serve_forever()

