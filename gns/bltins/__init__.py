import os
from .. import plugins


##### Public methods #####
def load_builtins(config_dict):
    return plugins.load_plugins(config_dict, os.path.dirname(__file__), "gns.bltins.", "bmod_", "BUILTINS_MAP")

