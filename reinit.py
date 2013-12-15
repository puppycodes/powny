#!/usr/bin/env pypy3


from ulib import optconf

from raava import const
from raava import zoo
from raava import service
from raava import application


##### Public constants #####
REINIT_SECTION = "reinit"


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
    parser.add_raw_argument("--do-it-now", dest="do_flag", action="store_true")
    options = parser.sync((service.MAIN_SECTION, REINIT_SECTION))[0]

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

    application.init_logging(
        options[service.OPTION_LOG_LEVEL],
        options[service.OPTION_LOG_FILE],
    )
    client = zoo.connect(options[service.OPTION_ZOO_NODES])
    zoo.drop(client, True)
    zoo.init(client, True)


##### Main #####
if __name__ == "__main__":
    main()

