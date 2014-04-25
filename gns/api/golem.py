import sys
import json
import cherrypy

import chrpc.server

from ulib import validators
import ulib.validators.common # pylint: disable=W0611

from . import common


##### Private methods #####
def _error_page(status, message, traceback, version):
    (err, info) = sys.exc_info()[:2]
    cherrypy.response.headers["Content-Type"] = "text/plain"
    return "error: {}: {}".format(err.__name__, info)


##### Public classes #####
class SubmitApi(chrpc.server.WebObject):
    """ This class implements compatibility with handle http://nda.ya.ru/3QTLzG """

    exposed = True
    _cp_config = {
        "error_page.default": _error_page,
    }

    def __init__(self, config):
        self._config = config


    ##### Override #####

    def GET(self, **kwargs): # pylint: disable=C0103
        return self._handle(kwargs)

    def POST(self, **kwargs): # pylint: disable=C0103
        for (key, value) in kwargs.items():
            if isinstance(value, (list, tuple)):
                kwargs[key] = value[-1]
        return self._handle(kwargs)


    ##### Private #####

    def _handle(self, request):
        event = {
            "host":    request["object"],
            "service": request["eventtype"],
        }
        if validators.common.valid_bool(request.get("json", False)):
            event.update(json.loads(request.get("info", "{}")))
        else:
            event.update({
                    "status": {
                        "ok":       "OK",
                        "warning":  "WARN",
                        "critical": "CRIT",
                    }[request.get("status", "critical")],
                    "description": request.get("info", ""),
                })
        try:
            job_id = common.add_event(event, self._config)
            return "ok job_id:" + job_id
        except common.InputOverflowError:
            raise cherrypy.HTTPError(503, "Input overflow")
