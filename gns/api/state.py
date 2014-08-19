import cherrypy
import chrpc.server

from raava import appstate
from raava import events

from .. import zclient


##### Public classes #####
class StateResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config):
        self._config = config

    @cherrypy.tools.json_out()
    def GET(self): # pylint: disable=C0103
        with zclient.get_context(self._config) as client:
            state = appstate.get_state(client)
            state["sizes"] = {
                "input":   events.get_input_size(client),
                "ready":   events.get_ready_size(client),
                "running": events.get_running_size(client),
            }
            return state
