#!/usr/bin/env python


import logging

from gns import service
from gns import fetchers


##### Private objects #####
_logger = logging.getLogger("gns.fetchers")


##### Public methods #####
def main():
    (config, parser, argv) = service.init(description="GNS rules fetcher")
    parser.add_argument("--do-it-now", dest="do_flag", action="store_true")
    options = parser.parse_args(argv)

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

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

