#!/usr/bin/env pypy3


import json
import logging

import ulib.optconf

import raava.const
import raava.zoo
import raava.application
import raava.events
import raava.rules

import gns.const
import gns.service


##### Private objects #####
_logger = logging.getLogger(raava.const.LOGGER_NAME)


##### Public methods #####
def main():
    parser = ulib.optconf.OptionsConfig(
        (
            gns.service.OPTION_LOG_FILE,
            gns.service.OPTION_LOG_LEVEL,
            gns.service.OPTION_ZOO_NODES,
        ),
        gns.const.CONFIG_FILE,
    )
    parser.add_arguments(
        gns.service.ARG_LOG_FILE,
        gns.service.ARG_LOG_LEVEL,
        gns.service.ARG_ZOO_NODES,
    )
    parser.add_raw_argument("--add",    dest="add_handler_type", action="store", metavar="<handler_type>")
    parser.add_raw_argument("--cancel", dest="cancel_job_id",    action="store", metavar="<uuid>")
    parser.add_raw_argument("--info",   dest="info_job_id",      action="store", metavar="<uuid>")
    options = parser.sync((gns.service.SECTION.MAIN, gns.service.SECTION.RCLI))[0]

    raava.application.init_logging(
        options[gns.service.OPTION_LOG_LEVEL],
        options[gns.service.OPTION_LOG_FILE],
    )
    client = raava.zoo.connect(options[gns.service.OPTION_ZOO_NODES])

    if not options.add_handler_type is None:
        raava.zoo.init(client)
        print(raava.events.add(client, raava.rules.EventRoot(json.loads(input())), options.add_handler_type))
    elif not options.cancel_job_id is None:
        raava.zoo.init(client)
        raava.events.cancel(client, options.cancel_job_id)
    elif not options.info_job_id is None:
        raava.zoo.init(client)
        print(json.dumps(raava.events.info(client, options.info_job_id), sort_keys=True, indent=4))


##### Main #####
if __name__ == "__main__":
    main()

