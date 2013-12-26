#!/usr/bin/env pypy3


import ulib.optconf

import raava.zoo

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
    parser.add_raw_argument("--do-it-now", dest="do_flag", action="store_true")
    options = parser.sync(("main", "reinit"))[0]

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

    gns.service.init_logging(options)
    client = raava.zoo.connect(options[gns.service.OPTION_ZOO_NODES])
    raava.zoo.drop(client, True)
    raava.zoo.init(client, True)


##### Main #####
if __name__ == "__main__":
    main()

