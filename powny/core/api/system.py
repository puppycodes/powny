from .. import tools
from .. import optconf

from . import Resource


# =====
class StateResource(Resource):
    name = "Show the system state"

    def __init__(self, pool):
        self._pool = pool

    def process_request(self):
        """
            GET -- Returns some information about the system state:
                       # =====
                       {
                           "jobs": {
                               "input": <number>,
                               "all":   <number",
                           },
                       }
                       # =====
        """

        with self._pool.get_backend() as backend:
            return {
                "jobs": {
                    "input": backend.jobs_control.get_input_size(),
                    "all":   backend.jobs_control.get_jobs_count(),
                    "apps":  backend.system_apps_state.get_full_state(),
                },
            }


class InfoResource(Resource):
    name = "The system information"

    def __init__(self, pool):
        self._pool = pool

    def process_request(self):
        """
            GET -- Returns some information about the system in format:
                       # =====
                       {
                           "version": "<digits.and.dots>",
                           "backend": {
                               "name": "<backend_name>",
                               "info": {...},  # Backen-specific data
                           },
                       }
                       # =====
        """

        with self._pool.get_backend() as backend:
            return {
                "version": tools.get_version(),
                "backend": {
                    "name": self._pool.get_backend_name(),
                    "info": backend.get_info(),
                },
            }


class ConfigResource(Resource):
    name = "The system configuration"

    def __init__(self, config):
        self._public = self._make_public(config)

    def process_request(self):
        """
            GET -- Returns a dictionary with the system configuration except
                   some secret options (passwords, tokens, etc.).
        """
        return self._public

    def _make_public(self, config):
        public = {}
        for (key, value) in config.items():
            if isinstance(value, optconf.Section):
                public[key] = self._make_public(value)
            elif not config._is_secret(key):  # pylint: disable=protected-access
                public[key] = value
        return public
