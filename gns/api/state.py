import cherrypy
import chrpc.server

from raava import appstate

from .. import zclient


##### Public classes #####
class StateResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config):
        self._config = config

    @cherrypy.tools.json_out()
    def GET(self): # pylint: disable=C0103
        with zclient.get_context(self._config) as client:
            return appstate.get_state(client)
