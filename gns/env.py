import threading
import copy
import textwrap
import mako.template

from ulib import typetools

from . import service


##### Private objects #####
_config = None
_config_lock = threading.Lock()


##### Public methods #####
def setup_config(config):
    with _config_lock:
        global _config
        _config = copy.copy(config)


###
def get_config(*keys_list, default=None):
    if len(keys_list) == 0:
        return _config
    value = _config
    for key in keys_list:
        if key in value:
            value = value[key]
        else:
            return default
    return value

def patch_config(pattern):
    with _config_lock:
        global _config
        assert _config is not None, "Run setup_config() first"
        config = copy.copy(_config)
        defaults = service.make_default_config(pattern)
        typetools.merge_dicts(config, typetools.merge_dicts(defaults, config))
        service.validate_config(config, pattern)
        _config = config


###
def format_event(template, event_root):
    return mako.template.Template(textwrap.dedent(template).strip()).render(event=event_root)

