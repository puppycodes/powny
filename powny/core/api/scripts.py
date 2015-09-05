import re

from flask import request

from . import (
    get_exposed,
    Resource,
    ApiError,
)


# =====
class ExposedScriptsResource(Resource):
    name = "Information about scripts"
    docstring = """
        GET  -- Returns a current version (head) of the scripts in format:

                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {
                        "head":    "<HEAD>"
                        "errors":  {"<path.to.module>": "<Traceback>", ...}
                        "exposed": ["<path.to.function>", ...]|null,
                    },
                }
                # =====

                @head    -- Current version of the scripts. Null if the version has not yet been set.
                @errors  -- Errors that occurred while loading the specified modules (null if global error occurs).
                @exposed -- List of functions that can be called directly by name (null if global error occurs).

                Possible errors (with status=="error"):
                    503 -- Non-existant HEAD for scripts.
    """

    def __init__(self, pool, loader):
        self._pool = pool
        self._loader = loader

    def process_request(self):
        backend = self._pool.get_backend()
        try:
            if request.method == "GET":
                (head, exposed, errors, exc) = get_exposed(backend, self._loader)
                if exc is None:  # No errors
                    # exposed is None if HEAD is not configured
                    exposed_names = (list(exposed) if exposed is not None else None)
                    return ({"head": head, "exposed": exposed_names, "errors": errors}, "The scripts of current HEAD")
                else:
                    raise ApiError(503, exc, {"head": head, "exposed": None, "errors": None})
        finally:
            self._pool.retrieve_backend(backend)


class ScriptsHeadResource(Resource):
    name = "Operations with scripts HEAD"
    methods = ("GET", "POST")
    docstring = """
        GET  -- Returns a current version (head) of the scripts in format:

                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {"head": "<HEAD>"|null},
                }
                # =====

                @head -- Current version of the scripts. Null if the version has not yet been set.

        POST -- Takes a version (head) in the format: {"head": "<HEAD>"} and applies it.

                Return value:
                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {"head": "<HEAD>"},
                }
                # =====

                Possible POST errors (with status=="error"):
                    400 -- Invalid HEAD (not a hex string).
    """

    def __init__(self, pool):
        self._pool = pool

    def process_request(self):
        backend = self._pool.get_backend()
        try:
            if request.method == "GET":
                return self._request_get(backend)
            elif request.method == "POST":
                return self._request_post(backend)
        finally:
            self._pool.retrieve_backend(backend)

    def _request_post(self, backend):
        head = str((request.data or {}).get("head")).strip()
        if re.match(r"^[0-9a-fA-F]+$", head) is None:
            raise ApiError(400, "The HEAD must be a hex string", {"head": head})
        backend.scripts.set_head(head)
        return ({"head": head}, "The HEAD has been updated")

    def _request_get(self, backend):
        return ({"head": backend.scripts.get_head()}, "Current HEAD")
