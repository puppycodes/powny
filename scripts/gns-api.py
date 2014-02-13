#!/usr/bin/env python


import cherrypy

from chrpc.server import Module
from gns import service

from gns import api
import gns.api.rpc.events # pylint: disable=W0611
import gns.api.rest.jobs
import gns.api.compat.golem


##### Public methods #####
def application(environ, start_response):
    (root, server_opts) = _init(service.S_API)
    cherrypy.tree.mount(root, "/", server_opts)
    return cherrypy.tree(environ, start_response)

def run_local():
    (root, server_opts) = _init(service.S_CHERRY)
    cherrypy.quickstart(root, config=server_opts)


##### Private methods #####
def _init(section):
    config = service.init(description="GNS HTTP API")[0]
    (root, app_opts) = _make_tree(config)
    server_opts = config[section].copy()
    server_opts.update(app_opts)
    return (root, server_opts)

def _make_tree(config):
    root = Module()
    root.api = Module()

    root.api.rpc = Module()
    root.api.rpc.v1 = Module()
    root.api.rpc.v1.events = api.rpc.events.EventsApi(config)

    root.api.rest = Module()
    root.api.rest.v1 = Module()
    root.api.rest.v1.jobs = api.rest.jobs.JobsApi(config)

    root.api.compat = Module()
    root.api.compat.golem = Module()
    root.api.compat.golem.submit = api.compat.golem.SubmitApi(config)

    disp_dict = { "request.dispatch": cherrypy.dispatch.MethodDispatcher() }
    return (root, {
            "/api/rest/v1/jobs":        disp_dict,
            "/api/compat/golem/submit": disp_dict,
        })


##### Main #####
if __name__ == "__main__":
    run_local()

