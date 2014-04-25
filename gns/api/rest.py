import cherrypy
import decorator
import chrpc.server

from ulib import validatorlib
from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.extra

from raava import events

from . import common
from .. import zclient


##### Private methods #####
def _raise_http(method):
    def wrap(method, *args, **kwargs):
        try:
            return method(*args, **kwargs)
        except validatorlib.ValidatorError as err:
            raise cherrypy.HTTPError(400, str(err))
        except events.NoJobError:
            raise cherrypy.HTTPError(404, "No job")
        except common.InputQueueOverflowError:
            raise cherrypy.HTTPError(503, "Input queue overflow")
    return decorator.decorator(wrap, method)


##### Public classes #####
class JobsResource(chrpc.server.WebObject):
    exposed = True

    def __init__(self, config):
        self._config = config

    @_raise_http
    @cherrypy.tools.json_out()
    def GET(self, job_id = None): # pylint: disable=C0103
        job_id = validators.common.valid_maybe_empty(job_id, validators.extra.valid_uuid)
        with zclient.get_context(self._config) as client:
            if job_id is None:
                return events.get_jobs(client)
            else:
                return events.get_info(client, job_id)

    @_raise_http
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self): # pylint: disable=C0103
        job_id = common.add_event(cherrypy.request.json, self._config)
        return {"status": "ok", "id": job_id}

    @_raise_http
    @cherrypy.tools.json_out()
    def DELETE(self, job_id): # pylint: disable=C0103
        job_id = validators.extra.valid_uuid(job_id)
        with zclient.get_context(self._config) as client:
            events.cancel(client, job_id)
        return {"status": "ok"}
