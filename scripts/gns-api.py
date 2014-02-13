#!/usr/bin/env python


import copy
import cherrypy

from chrpc.server import Module
from gns import service

from gns import api
import gns.api.rpc.events # pylint: disable=W0611
import gns.api.rest.jobs
import gns.api.compat.golem


##### Public methods #####
def application(environ, start_response):
    (root, server_dict) = _init(service.S_API)
    cherrypy.tree.mount(root, "/", server_dict)
    return cherrypy.tree(environ, start_response)

def run_local():
    (root, server_dict) = _init(service.S_CHERRY)
    cherrypy.quickstart(root, config=server_dict)


##### Private methods #####
def _init(section):
    config_dict = service.init(description="GNS HTTP API")[0]
    (root, app_dict) = _make_tree(config_dict)
    server_dict = copy.deepcopy(config_dict[section])
    server_dict.update(app_dict)
    return (root, server_dict)

def _make_tree(config_dict):
    root = Module()
    root.api = Module()

    root.api.rpc = Module()
    root.api.rpc.v1 = Module()
    root.api.rpc.v1.events = api.rpc.events.Api(config_dict)

    root.api.rest = Module()
    root.api.rest.v1 = Module()
    root.api.rest.v1.jobs = api.rest.jobs.Jobs(config_dict)

    root.api.compat = Module()
    root.api.compat.golem = Module()
    root.api.compat.golem.submit = api.compat.golem.Submit(config_dict)

    disp = ( lambda: {"request.dispatch": cherrypy.dispatch.MethodDispatcher()} )
    return (root, {
            "/api/rest/v1/jobs":        disp(),
            "/api/compat/golem/submit": disp(),
        })


##### Main #####
if __name__ == "__main__":
    run_local()

