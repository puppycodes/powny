import os
from .. import plugins


##### Public methods #####
def load_fetchers(config_dict):
    return plugins.load_plugins(config_dict, os.path.dirname(__file__), "gns.fetchers.", "fmod_", "FETCHERS_MAP")

