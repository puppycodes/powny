import cherrypy

from ulib import validators
import ulib.validators.extra

from raava import zoo
from raava import events
from raava import rules

from gns import service
from gns import chain

class Jobs:
    exposed = True

    def __init__(self, zoo_nodes):
        self._zoo_nodes = zoo_nodes

    @cherrypy.tools.json_out()
    def GET(self, job_id=None):
        with zoo.Connect(self._zoo_nodes) as client:
            if job_id == None:
                return events.get_jobs(client)
            else:
                job_id = validators.extra.validUuid(job_id)
                return events.get_info(client, job_id)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self):
        kwargs = cherrypy.request.json
        event_root = rules.EventRoot(kwargs)
        with zoo.Connect(self._zoo_nodes) as client:
            job_id = events.add(client, event_root, chain.MAIN)
        return {'status': 'ok', 'id': job_id}

    @cherrypy.tools.json_out()
    def DELETE(self, job_id):
        job_id = validators.extra.validUuid(job_id)
        with zoo.Connect(self._zoo_nodes) as client:
            events.cancel(client, job_id)
        return {'status': 'ok'}


def main():
    config = service.init(description="GNS HTTP API")[0]
    zoo_nodes = config[service.S_CORE][service.O_ZOO_NODES]
    app_config = config[service.S_CHERRY]
    app_config.update({'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}})
    cherrypy.quickstart(Jobs(zoo_nodes), '/api/v2/jobs', app_config)

if __name__ == '__main__':
    main()
