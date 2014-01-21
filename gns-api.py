#!/usr/bin/env python


import cherrypy
import ulib.optconf

import raava.zoo
import chrpc.server

import gns.service
import gns.api.events


##### Public methods #####
def main():
    parser = ulib.optconf.OptionsConfig(
        gns.service.ALL_OPTIONS,
        gns.const.CONFIG_FILE,
    )
    parser.add_arguments(
        gns.service.ARG_LOG_FILE,
        gns.service.ARG_LOG_LEVEL,
        gns.service.ARG_LOG_FORMAT,
        gns.service.ARG_ZOO_NODES,
    )
    parser.add_raw_argument("--port", dest="port", action="store", type=int, default=8080, metavar="<port>")
    options = parser.sync(("main", "api"))[0]

    gns.service.init_logging(options)

    with raava.zoo.Connect(options[gns.service.OPTION_ZOO_NODES]) as client:
        raava.zoo.init(client)

    root = chrpc.server.Module()
    root.api = chrpc.server.Module()
    root.api.v1 = chrpc.server.Module()
    root.api.v1.events = gns.api.events.Api(options[gns.service.OPTION_ZOO_NODES])

    cherrypy.quickstart(root, config={
            "global": {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": options.port,
            },
        })


##### Main #####
if __name__ == "__main__":
    main()

