from raava import rhooks
from raava import handlers

from . import service
from . import bltins
from . import env


##### Public methods #####
def init_rules_environment(config):
    rhooks.setup_builtins(bltins.load_builtins(config))
    env.setup_config(config)

    rules_path = config[service.S_CORE][service.O_RULES_DIR]
    import_alias = config[service.S_CORE][service.O_IMPORT_ALIAS]

    handlers.setup_path(rules_path)
    if import_alias is not None:
        handlers.setup_import_alias(import_alias, rules_path)

