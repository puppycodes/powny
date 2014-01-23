#!/usr/bin/env python


import cherrypy

import raava.zoo
import chrpc.server

import gns.service
import gns.api.events


##### Public methods #####
def main():
    config_dict = gns.service.init(description="GNS HTTP API")[0]
    with raava.zoo.Connect(config_dict[gns.service.S_CORE][gns.service.O_ZOO_NODES]) as client:
        raava.zoo.init(client)

    root = chrpc.server.Module()
    root.api = chrpc.server.Module()
    root.api.v1 = chrpc.server.Module()
    root.api.v1.events = gns.api.events.Api(config_dict[gns.service.S_CORE][gns.service.O_ZOO_NODES])

    cherrypy.quickstart(root, config={
            "global": {
                "server.socket_host": config_dict[gns.service.S_API][gns.service.O_HOST],
                "server.socket_port": config_dict[gns.service.S_API][gns.service.O_PORT],
            },
        })


##### Main #####
if __name__ == "__main__":
    main()

