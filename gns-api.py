#!/usr/bin/env python


import cherrypy
#from raava import zoo
from gns import service
from chrpc.server import Module

from gns import api
import gns.api.events # pylint: disable=W0611


##### Public methods #####
def application(environ, start_response):
    (root, config_dict) = _init()
    cherrypy.tree.mount(root, "/", ( config_dict[service.S_API] or None ))
    return cherrypy.tree(environ, start_response)

def run_local():
    (root, config_dict) = _init()
    cherrypy.quickstart(root, config=( config_dict[service.S_CHERRY] or None ))


##### Private methods #####
def _init():
    config_dict = service.init(description="GNS HTTP API")[0]
    #with zoo.Connect(config_dict[service.S_CORE][service.O_ZOO_NODES]) as client:
    #    zoo.init(client)
    return (_make_tree(config_dict), config_dict)

def _make_tree(config_dict):
    root = Module()
    root.api = Module()
    root.api.v1 = Module()
    root.api.v1.events = api.events.Api(config_dict)
    return root


##### Main #####
if __name__ == "__main__":
    run_local()

