#!/usr/bin/env python


from raava import zoo

from gns import service
from gns import zclient


##### Public methods #####
def main():
    (config, parser, argv) = service.init(description="Re-init ZooKeeper GNS storage")
    parser.add_argument("--do-it-now", action="store_true", required=True, help="Specify this option to process")
    parser.parse_args(argv) # Handle --do-it-now and --help

    with zclient.get_context(config) as client:
        zoo.drop(client, True)
        zoo.init(client, True)


##### Main #####
if __name__ == "__main__":
    main()

