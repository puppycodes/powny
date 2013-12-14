#!/usr/bin/env pypy3


import sys
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


##### Public methods #####
def main():
    config = optconf.OptionsConfig((
            service.OPTION_LOG_FILE,
            service.OPTION_LOG_LEVEL,
            service.OPTION_ZOO_NODES,
        ),
        sys.argv[1:],
        const.CONFIG_FILE,
    )
    config.add_arguments(
        service.ARG_LOG_FILE,
        service.ARG_LOG_LEVEL,
        service.ARG_ZOO_NODES,
    )
    config.parser().add_argument("--add",    dest="add_handler_type", action="store", metavar="<handler_type>")
    config.parser().add_argument("--cancel", dest="cancel_job_id",      action="store_true")
    options = config.sync((service.MAIN_SECTION,))

    application.init_logging(
        options[service.OPTION_LOG_LEVEL],
        options[service.OPTION_LOG_FILE],
    )
    client = zoo.connect(options[service.OPTION_ZOO_NODES])

    if not options.add_handler_type is None:
        zoo.init(client)
        events.add(client, rules.EventRoot(json.loads(input())), options.add_handler_type)
    elif options.cancel_job_id:
        zoo.init(client)
        events.cancel(client, options.cancel_job_id)


##### Main #####
if __name__ == "__main__":
    main()

