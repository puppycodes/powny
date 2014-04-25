from raava import events
from raava import rules

from .. import service
from .. import zclient
from .. import chain


##### Exceptions #####
class InputOverflowError(Exception):
    pass


##### Public methods #####
def add_event(event, config):
    event_root = rules.EventRoot(event)
    with zclient.get_context(config) as client:
        if events.get_input_size(client) >= config[service.S_CORE][service.O_MAX_INPUT_QUEUE_SIZE]:
            raise InputOverflowError
        job_id = events.add(client, event_root, chain.MAIN)
    return job_id
