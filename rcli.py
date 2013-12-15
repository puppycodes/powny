#!/usr/bin/env pypy3


import json
import logging

from ulib import optconf

from raava import const
from raava import zoo
from raava import service
from raava import application
from raava import events
from raava import rules


##### Private objects #####
_logger = logging.getLogger(const.LOGGER_NAME)


##### Public constants #####
RCLI_SECTION = "rcli"


##### Public methods #####
def main():
    parser = optconf.OptionsConfig((
            service.OPTION_LOG_FILE,
            service.OPTION_LOG_LEVEL,
            service.OPTION_ZOO_NODES,
        ),
        const.CONFIG_FILE,
    )
    parser.add_arguments(
        service.ARG_LOG_FILE,
        service.ARG_LOG_LEVEL,
        service.ARG_ZOO_NODES,
    )
    parser.add_raw_argument("--add",    dest="add_handler_type", action="store", metavar="<handler_type>")
    parser.add_raw_argument("--cancel", dest="cancel_job_id",    action="store", metavar="<uuid>")
    parser.add_raw_argument("--info",   dest="info_job_id",      action="store", metavar="<uuid>")
    options = parser.sync((service.MAIN_SECTION, RCLI_SECTION))[0]

    application.init_logging(
        options[service.OPTION_LOG_LEVEL],
        options[service.OPTION_LOG_FILE],
    )
    client = zoo.connect(options[service.OPTION_ZOO_NODES])

    if not options.add_handler_type is None:
        zoo.init(client)
        print(events.add(client, rules.EventRoot(json.loads(input())), options.add_handler_type))
    elif not options.cancel_job_id is None:
        zoo.init(client)
        events.cancel(client, options.cancel_job_id)
    elif not options.info_job_id is None:
        zoo.init(client)
        print(json.dumps(events.info(client, options.info_job_id), sort_keys=True, indent=4))


##### Main #####
if __name__ == "__main__":
    main()

