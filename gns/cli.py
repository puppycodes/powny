import importlib

from . import service


##### Public methods #####
def main():
    (config, parser, argv) = service.init()
    parser.add_argument(dest="command")
    options = parser.parse_args(argv)
    importlib.import_module("." + options.command, __package__).run(config)


##### Main #####
if __name__ == "__main__":
    main()

