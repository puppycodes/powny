import os
import importlib

from ulib import typetools

from .. import service


##### Public methods #####
def load_builtins(config_dict):
    builtins_dict = {}

    for file_name in os.listdir(__path__[0]):
        if file_name[0] in (".", "_") or not file_name.startswith("bmod_"):
            continue
        if os.path.isdir(os.path.join(__path__[0], file_name)):
            module_name = file_name
        elif file_name.lower().endswith(".py"):
            module_name = file_name[:file_name.lower().index(".py")]
        else:
            continue

        module = importlib.import_module("gns.bltins." + module_name)
        module = importlib.import_module("gns.bltins." + module_name)

        typetools.merge_dicts(builtins_dict, getattr(module, "BUILTINS_MAP"))
        std_dict = getattr(module, "CONFIG_MAP", None)
        if std_dict is not None:
            default_dict = service.make_default_config(std_dict)
            typetools.merge_dicts(config_dict, typetools.merge_dicts(default_dict, config_dict))
            service.validate_config(config_dict, std_dict)

    return builtins_dict

