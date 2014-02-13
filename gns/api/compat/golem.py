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


##### Private constants #####
_EVENTS_PATH = "/golem_compat"


##### Private methods #####
def _error_page(status, message, traceback, version):
    (err, text) = sys.exc_info()[:2]
    cherrypy.response.headers["Content-Type"] = "text/plain"
    return "error: {}: {}".format(err.__name__, str(text))


##### Public classes #####
class Submit(chrpc.server.WebObject):
    exposed = True
    _cp_config = {
        "error_page.default": _error_page,
    }

    def __init__(self, config_dict):
        self._nodes_list = config_dict[service.S_CORE][service.O_ZOO_NODES]


    ##### Private #####

    def GET(self, **request_dict):
        return self._submit_event(request_dict)

    def POST(self, **request_dict):
        for (key, value) in request_dict.items():
            if isinstance(value, (list, tuple)):
                request_dict[key] = value[-1]
        return self._submit_event(request_dict)

    ###

    def _submit_event(self, request_dict):
        event_root = rules.EventRoot({
                "host_name":    request_dict["object"],
                "service_name": request_dict["eventtype"],
            })
        if validators.common.validBool(request_dict.get("json", False)):
            event_root.update(json.loads(request_dict["info"]))
        else:
            event_root.update({
                    "status": {
                        "ok":       "OK",
                        "warning":  "WARN",
                        "critical": "CRIT",
                    }[request_dict.get("status", "critical")],
                    "description": request_dict["info"],
                })
        return "ok job_id:" + self._replace_event(event_root)

    def _replace_event(self, event_root):
        check_id = typetools.object_hash((event_root["host_name"], event_root["service_name"]))
        check_path = zoo.join(_EVENTS_PATH, check_id)
        with zoo.Connect(self._nodes_list) as client:
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

