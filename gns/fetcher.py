#!/usr/bin/env python


import logging

from . import service
from . import fetchers


##### Private objects #####
_logger = logging.getLogger("gns.fetchers")


##### Public methods #####
def main():
    (config, parser, argv) = service.init(description="GNS rules fetcher")
    parser.add_argument("--do-it-now", action="store_true", required=True, help="Specify this option to process")
    parser.parse_args(argv) # Handle --do-it-now and --help

    fetcher_name = config[service.S_CORE][service.O_FETCHER]
    if fetcher_name is None:
        _logger.debug("Fetcher is not configured")
        return

    try:
        fetcher = fetchers.load_fetchers(config)[fetcher_name]
        fetchers.replace_head(
            config[service.S_CORE][service.O_RULES_DIR],
            config[service.S_CORE][service.O_RULES_HEAD],
            fetcher(config),
        )
    except Exception:
        _logger.exception("Cannot update rules")
        raise


##### Main #####
if __name__ == "__main__":
    main()

