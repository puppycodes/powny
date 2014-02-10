import os
import importlib

from ulib import typetools

from .. import service


##### Public methods #####
def load_plugins(config_dict, package_prefix, module_prefix, mapper):
    plugins_dict = {}

    for file_name in os.listdir(__path__[0]):
        if file_name[0] in (".", "_") or not file_name.startswith(module_prefix):
            continue
        if os.path.isdir(os.path.join(__path__[0], file_name)):
            module_name = file_name
        elif file_name.lower().endswith(".py"):
            module_name = file_name[:file_name.lower().index(".py")]
        else:
            continue

        module = importlib.import_module(package_prefix + module_name)

        typetools.merge_dicts(plugins_dict, getattr(module, mapper))
        std_dict = getattr(module, "CONFIG_MAP", None)
        if std_dict is not None:
            default_dict = service.make_default_config(std_dict)
            typetools.merge_dicts(config_dict, typetools.merge_dicts(default_dict, config_dict))
            service.validate_config(config_dict, std_dict)

    return plugins_dict

