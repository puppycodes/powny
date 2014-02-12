import cherrypy

import chrpc.server

from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.extra

from raava import zoo
from raava import events
from raava import rules

from ... import service
from ... import chain


##### Public classes #####
class Jobs(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config_dict):
        self._nodes_list = config_dict[service.S_CORE][service.O_ZOO_NODES]

    @cherrypy.tools.json_out()
    def GET(self, job_id = None):
        job_id = validators.common.valid_maybe_empty(job_id, validators.extra.valid_uuid)
        with zoo.Connect(self._nodes_list) as client:
            if job_id is None:
                return events.get_jobs(client)
            else:
                return events.get_info(client, job_id)

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        event_root = rules.EventRoot(cherrypy.request.json)
        with zoo.Connect(self._nodes_list) as client:
            job_id = events.add(client, event_root, chain.MAIN)
        return {"status": "ok", "id": job_id}

    @cherrypy.tools.json_out()
    def DELETE(self, job_id):
        job_id = validators.extra.valid_uuid(job_id)
        with zoo.Connect(self._nodes_list) as client:
            events.cancel(client, job_id)
        return {"status": "ok"}

