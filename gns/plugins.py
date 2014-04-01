import os
import importlib

from ulib import typetools

from . import env


##### Public methods #####
def load_plugins(config, path, package_prefix, module_prefix, mapper):
    plugins = {}

    for file_name in os.listdir(path):
        if file_name[0] in (".", "_") or not file_name.startswith(module_prefix):
            continue
        if os.path.isdir(os.path.join(path, file_name)):
            module_name = file_name
        elif file_name.lower().endswith(".py"):
            module_name = file_name[:file_name.lower().index(".py")]
        else:
            continue

        module = importlib.import_module(package_prefix + module_name)

        typetools.merge_dicts(plugins, getattr(module, mapper))
        pattern = getattr(module, "CONFIG_MAP", None)
        if pattern is not None:
            env.patch_config(pattern)

    return plugins

