from raava import handlers
from raava import events

from . import service
from . import zclient
from . import env


##### Public methods #####
def init_rules_environment(config):
    env.setup_config(config)

    rules_path = config[service.S_CORE][service.O_RULES_DIR]
    import_alias = config[service.S_CORE][service.O_IMPORT_ALIAS]

    handlers.setup_path(rules_path)
    if import_alias is not None:
        handlers.setup_import_alias(import_alias, rules_path)


###
def get_events_counter(config):
    with zclient.get_context(config) as client:
        return events.get_events_counter(client)

def get_jobs_number(config):
    with zclient.get_context(config) as client:
        return len(events.get_jobs(client))

