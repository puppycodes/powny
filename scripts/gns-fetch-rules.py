#!/usr/bin/env python


import os
import logging

from gns import const
from gns import service
from gns import fetchers


##### Private objects #####
_logger = logging.getLogger(const.LOGGER_NAME)


##### Private methods #####
def _replace_head(rules_path, head_name, module_name):
    head_path = os.path.join(rules_path, head_name)
    tmp_path = os.path.join(rules_path, module_name + ".tmp")
    _logger.info("Updating the rules HEAD: %s -> %s", os.readlink(head_path), module_name)
    os.symlink(module_name, tmp_path)
    try:
        os.rename(tmp_path, head_path)
    except Exception:
        _logger.exception("Cannot rewrite the HEAD symlink")
        os.unlink(tmp_path)
        raise


##### Public methods #####
def main():
    (config_dict, parser, argv_list) = service.init(description="GNS rules fetcher")
    parser.add_argument("--do-it-now", dest="do_flag", action="store_true")
    options = parser.parse_args(argv_list)

    if not options.do_flag: # pylint: disable=E1101
        raise RuntimeError("Specify option --do-it-now to process")

    try:
        fetchers_dict = fetchers.load_fetchers(config_dict)
        fetcher = fetchers_dict[config_dict[service.S_CORE][service.O_FETCHER]]
        _replace_head(
            config_dict[service.S_CORE][service.O_RULES_DIR],
            config_dict[service.S_CORE][service.O_RULES_HEAD],
            fetcher(config_dict),
        )
    except Exception:
        _logger.exception("Cannot update rules")
        raise


##### Main #####
if __name__ == "__main__":
    main()

