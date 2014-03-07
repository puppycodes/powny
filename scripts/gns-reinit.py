#!/usr/bin/env python


from raava import zoo
from gns import service


##### Public methods #####
def main():
    (config, parser, argv_list) = service.init(description="Re-init ZooKeeper GNS storage")
    parser.add_argument("--do-it-now", dest="do_flag", action="store_true")
    options = parser.parse_args(argv_list)

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

    with zoo.Connect(config[service.S_CORE][service.O_ZOO_NODES]) as client:
        zoo.drop(client, True)
        zoo.init(client, True)


##### Main #####
if __name__ == "__main__":
    main()

