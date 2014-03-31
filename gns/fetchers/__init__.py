import os
import os.path
import logging

from .. import plugins


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public methods #####
def load_fetchers(config):
    return plugins.load_plugins(config, os.path.dirname(__file__), "gns.fetchers.", "fmod_", "FETCHERS_MAP")

def replace_head(rules_path, head_name, module_name):
    head_path = os.path.join(rules_path, head_name)
    if os.path.islink(head_path) and os.readlink(head_path) == module_name:
        _logger.debug("HEAD does not need to be updated")
        return
    tmp_path = os.path.join(rules_path, module_name + ".tmp")
    _logger.info("Updating the rules HEAD to %s", module_name)
    os.symlink(module_name, tmp_path)
    try:
        os.rename(tmp_path, head_path)
    except Exception:
        _logger.exception("Cannot rewrite the HEAD symlink")
        os.unlink(tmp_path)
        raise

