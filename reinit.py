#!/usr/bin/env pypy3


import sys

from ulib import optconf

from raava import const
from raava import zoo
from raava import service
from raava import application


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
    config.parser().add_argument("--do-it-now", dest="do_flag", action="store_true")
    options = config.sync((service.MAIN_SECTION,))

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

    application.init_logging(
        options[service.OPTION_LOG_LEVEL],
        options[service.OPTION_LOG_FILE],
    )
    client = zoo.connect(options[service.OPTION_ZOO_NODES])
    for path in (zoo.INPUT_PATH, zoo.READY_PATH, zoo.RUNNING_PATH, zoo.CONTROL_PATH):
        try:
            client.delete(path, recursive=True)
        except zoo.NoNodeError:
            pass
    zoo.init(client, True)


##### Main #####
if __name__ == "__main__":
    main()

