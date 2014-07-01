import cherrypy
import chrpc.server

from raava import events

from ulib import validatorlib
from ulib import validators
import ulib.validators.extra # pylint: disable=W0611

from .. import zclient


##### Public classes #####
class HeadResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config):
        self._config = config

    @cherrypy.tools.json_out()
    def GET(self): # pylint: disable=C0103
        with zclient.get_context(self._config) as client:
            # Supposed module_prefix is 'git_' (defined in docker-gitsplit postreceive hook) and should be constant
            head = events.get_head(client)
            last_commit = (head[len('git_'):] if head is not None else None)
            return {"head": last_commit}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self): # pylint: disable=C0103
        try:
            head = validators.extra.valid_hex_string(cherrypy.request.json["head"])
        except validatorlib.ValidatorError as err:
            raise cherrypy.HTTPError(400, str(err))
        with zclient.get_context(self._config) as client:
            events.set_head(client, "git_" + head)
        return {"head": head}
