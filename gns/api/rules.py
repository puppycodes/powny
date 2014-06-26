import cherrypy
import chrpc.server

from raava import events

from ulib import validatorlib
from ulib import validators
import ulib.validators.python # pylint: disable=W0611

from .. import zclient


##### Public classes #####
class HeadResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config):
        self._config = config

    @cherrypy.tools.json_out()
    def GET(self): # pylint: disable=C0103
        with zclient.get_context(self._config) as client:
            return {"head": events.get_head(client)}

    def POST(self, head): # pylint: disable=C0103
        try:
            head = validators.python.valid_object_name(head)
        except validatorlib.ValidatorError as err:
            raise cherrypy.HTTPError(400, str(err))
        with zclient.get_context(self._config) as client:
            events.set_head(client, head)
