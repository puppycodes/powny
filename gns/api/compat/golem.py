import sys
import json
import pickle
import uuid
import cherrypy

import chrpc.server

from ulib import typetools
from ulib import validators
import ulib.validators.common

from raava import zoo
from raava import events
from raava import rules

from ... import service
from ... import chain


##### Private methods #####
def _error_page(status, message, traceback, version):
    (err, text) = sys.exc_info()[:2]
    cherrypy.response.headers["Content-Type"] = "text/plain"
    return "error: {}: {}".format(err.__name__, str(text))


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
        if validators.common.validBool(request.get("json", False)):
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
        job_id = self._replace_event(event_root)
        return "ok job_id:" + job_id

    def _replace_event(self, event_root):
        check_id = typetools.object_hash((event_root["host_name"], event_root["service_name"]))
        check_path = zoo.join("/golem_compat", check_id)
        with zoo.Connect(self._zoo_nodes) as client:
            try:
                client.create(check_path, pickle.dumps(None), makepath=True)
            except zoo.NodeExistsError:
                pass
            with client.SingleLock(zoo.join(check_path, "lock")):
                old_job_id = client.pget(check_path)
                if old_job_id is not None:
                    try:
                        events.cancel(client, old_job_id)
                    except events.NoJobError:
                        pass
                new_job_id = str(uuid.uuid4())
                client.pset(check_path, new_job_id)
                events.add(client, event_root, chain.MAIN, job_id=new_job_id)
        return new_job_id

