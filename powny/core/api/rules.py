from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_hex_string

from .. import tools

from . import (
    ApiError,
    Resource,
)


# =====
class ExposedRulesResource(Resource):
    name = "Information about rules"
    docstring = """
        GET  -- Returns a current version (head) of the rules in format:

                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {
                        "head":    "<HEAD>"
                        "errors":  {"<path.to.module>": "<Traceback>", ...}
                        "exposed": {
                            "methods":  ["<path.to.function>", ...],
                            "handlers": ["<path.to.function>", ...],
                        },
                    },
                }
                # =====

                @head    -- Current version of the rules. Null if the version has not yet been set.
                @errors  -- Errors that occurred while loading the specified modules (null if global
                            error occurs).
                @exposed -- Functions loaded from the rules and ready for execution (null if global
                            error occurs).
                @exposed.methods  -- List of functions that can be called directly by name.
                @exposed.handlers -- List of event handlers that are selected based on filters.
                                     They may also be called manually as methods.

                Possible errors (with status=="error"):
                    503 -- Non-existant HEAD for rules.
    """

    def __init__(self, pool, loader):
        self._pool = pool
        self._loader = loader

    def process_request(self):
        with self._pool.get_backend() as backend:
            if request.method == "GET":
                (head, exposed, errors, exc) = tools.get_exposed(backend, self._loader)
                if exc is None:  # No errors
                    if exposed is not None:
                        exposed_names = {group: list(methods) for (group, methods) in exposed.items()}
                    else:
                        exposed_names = None  # Not configured HEAD
                    return ({"head": head, "exposed": exposed_names, "errors": errors}, "The rules of current HEAD")
                else:
                    raise ApiError(503, exc, {"head": head, "exposed": None, "errors": None})


class RulesHeadResource(Resource):
    name = "Operations with rules HEAD"
    methods = ("GET", "POST")
    docstring = """
        GET  -- Returns a current version (head) of the rules in format:

                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {"head": "<HEAD>"|null},
                }
                # =====

                @head -- Current version of the rules. Null if the version has not yet been set.

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
        with self._pool.get_backend() as backend:
            if request.method == "GET":
                return self._request_get(backend)
            elif request.method == "POST":
                return self._request_post(backend)

    def _request_post(self, backend):
        head = (request.data or {}).get("head")  # json
        try:
            head = valid_hex_string(head)
        except ValidatorError as err:
            raise ApiError(400, str(err), {"head": head})
        backend.rules.set_head(head)
        return ({"head": head}, "The HEAD has been updated")

    def _request_get(self, backend):
        return ({"head": backend.rules.get_head()}, "Current HEAD")
