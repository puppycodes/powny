from .. import tools
from .. import optconf

from . import Resource


# =====
class StateResource(Resource):
    name = "The system statistics"
    docstring = """
        GET -- Returns some information about the system state:
               # =====
               {
                   "status":  "ok",
                   "message": "<...>",
                   "result": {
                       "jobs": {
                           "input":    <number>,
                           "all":      <number>,
                       },
                       "apps": {
                           "<app_name>": {
                               "<node_name>" {
                                   "when":  "<time>",  # ISO-8601-like when statistics has been writed
                                   "pid":   <int>,
                                   "state": {
                                       "respawns": <int>,  # Number of restarts of the application
                                       ...  # Application-specific fields
                                   },
                               },
                           },
                           ...
                       },
                   },
               }
               # =====

               Application-specific fields:
                   worker:
                       processed -- Number of the processed jobs (exclude active);
                       active    -- Number of the current active jobs.
                   collector:
                       processed -- Number of the processed (removed or pushed-back) jobs.
    """

    def __init__(self, pool):
        self._pool = pool

    def process_request(self):
        with self._pool.get_backend() as backend:
            full_apps_state = backend.system_apps_state.get_full_state()
            full_apps_state.setdefault("worker", {})
            full_apps_state.setdefault("collector", {})
            result = {
                "jobs": {
                    "input": backend.jobs_control.get_input_size(),
                    "all": backend.jobs_control.get_jobs_count(),
                },
                "apps": full_apps_state,
            }
            return (result, self.name)


class InfoResource(Resource):
    name = "The system information"
    docstring = """
        GET -- Returns some information about the system in format:
               # =====
               {
                   "status":  "ok",
                   "message": "<...>",
                   "result":  {
                       "version": "<...>",
                       "backend": {
                           "name": "<backend_name>",
                           "info": {...},  # Backen-specific data
                       },
                   },
               }
               # =====
    """

    def __init__(self, pool):
        self._pool = pool

    def process_request(self):
        with self._pool.get_backend() as backend:
            result = {
                "version": tools.get_version(),
                "backend": {
                    "name": self._pool.get_backend_name(),
                    "info": backend.get_info(),
                },
            }
            return (result, self.name)


class ConfigResource(Resource):
    name = "The system configuration"
    docstring = """
        GET -- Returns a dictionary with the system configuration except
               some secret options (passwords, tokens, etc.):
               # =====
               {
                   "status":  "ok",
                   "message": "<...>",
                   "result":  {...},  # Dictionaries
               }
               # =====
    """

    def __init__(self, config):
        self._public = self._make_public(config)

    def process_request(self):
        return (self._public, self.name)

    def _make_public(self, config):
        public = {}
        for (key, value) in config.items():
            if isinstance(value, optconf.Section):
                public[key] = self._make_public(value)
            elif not config._is_secret(key):  # pylint: disable=protected-access
                public[key] = value
        return public
