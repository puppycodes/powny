import cherrypy
import chrpc.server

from raava import application
from raava import zoo

from .. import zclient


##### Private classes #####
class _StateResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, state_base_path, config):
        self._state_base_path = state_base_path
        self._config = config

    @cherrypy.tools.json_out()
    def GET(self):
        with zclient.get_context(self._config) as client:
            return application.get_state(client, self._state_base_path)


##### Public classes #####
class StateSplitterResource(_StateResource):
    def __init__(self, config):
        _StateResource.__init__(self, zoo.STATE_SPLITTER_PATH, config)

class StateWorkerResource(_StateResource):
    def __init__(self, config):
        _StateResource.__init__(self, zoo.STATE_WORKER_PATH, config)

class StateCollectorResource(_StateResource):
    def __init__(self, config):
        _StateResource.__init__(self, zoo.STATE_COLLECTOR_PATH, config)
