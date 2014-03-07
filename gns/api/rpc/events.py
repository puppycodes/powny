import chrpc.server

from ulib import validators
import ulib.validators.extra # pylint: disable=W0611

from raava import events
from raava import rules

from ... import zclient
from ... import chain


##### Public classes #####
class EventsApi(chrpc.server.Module):
    def __init__(self, config):
        self._config = config

    @chrpc.server.api
    def add(self, **kwargs):
        """ Submit event """
        event_root = rules.EventRoot(kwargs)
        with zclient.ClientContext(self._config) as client:
            return events.add(client, event_root, chain.MAIN)

    @chrpc.server.api
    def cancel(self, job_id):
        """ Cancel event by job id """
        job_id = validators.extra.valid_uuid(job_id)
        with zclient.ClientContext(self._config) as client:
            events.cancel(client, job_id)

    @chrpc.server.api
    def get_jobs(self):
        """ Jobs list """
        with zclient.ClientContext(self._config) as client:
            return events.get_jobs(client)

    @chrpc.server.api
    def get_finished(self, job_id):
        """ True if the job is finished else false """
        job_id = validators.extra.valid_uuid(job_id)
        with zclient.ClientContext(self._config) as client:
            return events.get_finished(client, job_id)

    @chrpc.server.api
    def get_info(self, job_id):
        """ Job info """
        job_id = validators.extra.valid_uuid(job_id)
        with zclient.ClientContext(self._config) as client:
            return events.get_info(client, job_id)

