#!/usr/bin/env python


import logging
import time

from . import service
from . import fetchers


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public methods #####
def run(config):
    fetcher_name = config[service.S_CORE][service.O_FETCHER]
    if fetcher_name is None:
        raise RuntimeError("Fetcher is not configured")
    fetcher = fetchers.load_fetchers(config)[fetcher_name]

    interval = config[service.S_CORE][service.O_FETCH_INTERVAL]
    if interval == 0:
        try:
            _update_rules(fetcher, config)
        except Exception:
            _logger.exception("Exception while rules fetching")
            raise
    else:
        # FIXME: this code is added to provide a way to run periodic task inside a container.
        # running cron or systemd timer is a better solution, but it demands additional research.
        _logger.info("Starting periodic rules fetching each %d seconds", interval)
        while True:
            next_fetch = time.time() + interval
            try:
                _update_rules(fetcher, config)
            except (SystemExit, KeyboardInterrupt):
                break # No traceback for this.
            except Exception:
                _logger.exception("Exception while rules fetching")
            time.sleep(next_fetch - time.time())
        _logger.info("Stopped rules fetching")


##### Private methods #####
def _update_rules(fetcher, config):
    try:
        module_name = fetcher(config)
        fetchers.replace_head(
            config[service.S_CORE][service.O_RULES_DIR],
            config[service.S_CORE][service.O_RULES_HEAD],
            module_name,
        )
    except Exception:
        _logger.error("Cannot update rules")
        raise
