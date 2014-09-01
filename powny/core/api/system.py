from .. import const
from .. import optconf


# =====
class StateResource:
    name = "Show the system state"

    def __init__(self, pool):
        self._pool = pool

    def handler(self):
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
                    "input": backend.jobs.control.get_input_size(),
                    "all":   backend.jobs.control.get_jobs_count(),
                    "apps":  backend.system.apps_state.get_full_state(),
                },
            }


class InfoResource:
    name = "The system information"

    def __init__(self, pool):
        self._pool = pool

    def handler(self):
        """
            GET -- Returns some information about the system in next format:
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
                "version": const.__version__,
                "backend": {
                    "name": self._pool.get_backend_name(),
                    "info": backend.get_info(),
                },
            }


class ConfigResource:
    name = "The system configuration"

    def __init__(self, config):
        self._public = self._make_public(config)

    def handler(self):
        """ GET -- Returns a dictionary with the system configuration """
        return self._public

    def _make_public(self, config):
        public = {}
        for (key, value) in config.items():
            if isinstance(value, optconf.Section):
                public[key] = self._make_public(value)
            elif not config._is_secret(key):  # pylint: disable=W0212
                public[key] = value
        return public
