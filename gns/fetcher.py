#!/usr/bin/env python


import logging
import time

from . import service
from . import fetchers


##### Private objects #####
_logger = logging.getLogger(__name__)

def run(config):
    fetcher_name = config[service.S_CORE][service.O_FETCHER]
    if fetcher_name is None:
        _logger.debug("Fetcher is not configured")
        return

    try:
        fetcher = fetchers.load_fetchers(config)[fetcher_name]
        rules_dir = config[service.S_CORE][service.O_RULES_DIR]
        rules_head = config[service.S_CORE][service.O_RULES_HEAD]
        fetch_interval = config[service.S_CORE][service.O_FETCH_INTERVAL]
        if fetch_interval == 0:
            module_name = fetcher(config)
            fetchers.replace_head(rules_dir, rules_head, module_name)
        else:
            # FIXME: this code is added to provide a way to run periodic task inside a container.
            # running cron or systemd timer is a better solution, but it demands additional research
            _logger.debug("Starting periodic rule fetching using %s to %s each %d seconds", fetcher_name, rules_dir, fetch_interval)
            while True:
                next_fetch = time.time() + fetch_interval
                module_name = fetcher(config)
                fetchers.replace_head(rules_dir, rules_head, module_name)
                time.sleep(next_fetch - time.time())

    except Exception:
        _logger.exception("Cannot update rules")
        raise
