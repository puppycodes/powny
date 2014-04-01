import argparse
import importlib
from . import service

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(dest="command")
    parser.add_argument("-c", "--config", dest="config_file_path", default=None, metavar="<file>")

    options = parser.parse_args()

    config = service.load_config(options.config_file_path)
    service.init_logging(config)
    service.init_meters(config)

    importlib.import_module("."+options.command, __package__).run(config)


if __name__ == "__main__":
    main()
