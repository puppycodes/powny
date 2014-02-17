import sys
import json
import cherrypy

import chrpc.server

from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from raava import zoo
from raava import events
from raava import rules

from ... import service
from ... import chain


##### Private methods #####
def _error_page(status, message, traceback, version):
    (err, info) = sys.exc_info()[:2]
    cherrypy.response.headers["Content-Type"] = "text/plain"
    return "error: {}: {}".format(err.__name__, info)


##### Public classes #####
class SubmitApi(chrpc.server.WebObject):
    """ This class implements compatibility with handle http://nda.ya.ru/3QTLzG """

    exposed = True
    _cp_config = {
        "error_page.default": _error_page,
    }

    def __init__(self, config):
        self._zoo_nodes = config[service.S_CORE][service.O_ZOO_NODES]


    ##### Override #####

    def GET(self, **kwargs):
        return self._handle(kwargs)

    def POST(self, **kwargs):
        for (key, value) in kwargs.items():
            if isinstance(value, (list, tuple)):
                kwargs[key] = value[-1]
        return self._handle(kwargs)


    ##### Private #####

    def _handle(self, request):
        event_root = rules.EventRoot({
                "host_name":    request["object"],
                "service_name": request["eventtype"],
            })
        if validators.common.valid_bool(request.get("json", False)):
            event_root.update(json.loads(request["info"]))
        else:
            event_root.update({
                    "status": {
                        "ok":       "OK",
                        "warning":  "WARN",
                        "critical": "CRIT",
                    }[request.get("status", "critical")],
                    "description": request["info"],
                })
        with zoo.Connect(self._zoo_nodes) as client:
            job_id = events.add(client, event_root, chain.MAIN)
        return "ok job_id:" + job_id

