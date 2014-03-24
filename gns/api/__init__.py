#!/usr/bin/env python


import cherrypy

from chrpc.server import Module
from .. import service

from . import rpc # pylint: disable=W0611
from . import rest
from . import golem


##### Public methods #####

# uWSGI entry point
def application(env, start_response):
    config = service.init(description="GNS HTTP API")[0]
    (root, app_opts) = _make_tree(config)
    server_opts = config[service.S_API].copy()
    server_opts.update(app_opts)
    cherrypy.tree.mount(root, "/", server_opts)
    return cherrypy.tree(env, start_response)

def main():
    config = service.init(description="GNS HTTP API")[0]
    (root, app_opts) = _make_tree(config)
    server_opts = config[service.S_CHERRY].copy()
    server_opts.update(app_opts)
    cherrypy.quickstart(root, config=server_opts)

def _make_tree(config):
    root = Module()
    root.api = Module()

    root.api.rpc = Module()
    root.api.rpc.v1 = Module()
    root.api.rpc.v1.events = rpc.EventsApi(config)

    root.api.rest = Module()
    root.api.rest.v1 = Module()
    root.api.rest.v1.jobs = rest.JobsResource(config)

    root.api.compat = Module()
    root.api.compat.golem = Module()
    root.api.compat.golem.submit = golem.SubmitApi(config)

    disp_dict = { "request.dispatch": cherrypy.dispatch.MethodDispatcher() }
    return (root, {
            "/api/rest/v1/jobs":        disp_dict,
            "/api/compat/golem/submit": disp_dict,
        })


##### Main #####
if __name__ == "__main__":
    main()
