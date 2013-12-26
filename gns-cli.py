#!/usr/bin/env pypy3


import json

import ulib.optconf

import raava.zoo
import raava.events
import raava.rules

import gns.const
import gns.service


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
    parser.add_raw_argument("--add",    dest="add_handler_type", action="store", metavar="<handler_type>")
    parser.add_raw_argument("--cancel", dest="cancel_job_id",    action="store", metavar="<uuid>")
    parser.add_raw_argument("--info",   dest="info_job_id",      action="store", metavar="<uuid>")
    options = parser.sync(("main", "rcli"))[0]

    gns.service.init_logging(options)

    client = raava.zoo.connect(options[gns.service.OPTION_ZOO_NODES])

    if options.add_handler_type is not None:
        raava.zoo.init(client)
        print(raava.events.add(client, raava.rules.EventRoot(json.loads(input())), options.add_handler_type))
    elif options.cancel_job_id is not None:
        raava.zoo.init(client)
        raava.events.cancel(client, options.cancel_job_id)
    elif options.info_job_id is not None:
        raava.zoo.init(client)
        print(json.dumps(raava.events.get_info(client, options.info_job_id), sort_keys=True, indent=4))


##### Main #####
if __name__ == "__main__":
    main()

