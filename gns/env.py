import textwrap
import mako.template


##### Private objects #####
_config_dict = None


##### Public methods #####
def setup_config(config_dict):
    global _config_dict
    _config_dict = config_dict


###
def get_config(*keys_list, default=None):
    if len(keys_list) == 0:
        return _config_dict
    value = _config_dict
    for key in keys_list:
        if key in value:
            value = value[key]
        else:
            return default
    return value


###
def format_event(template, event_root):
    return mako.template.Template(textwrap.dedent(template).strip()).render(event=event_root)

