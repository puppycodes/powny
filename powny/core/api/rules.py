from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_hex_string

from .. import tools

from . import (
    ApiError,
    Resource,
)


# =====
class RulesResource(Resource):
    name = "Operations with the rules HEAD"
    methods = ("GET", "POST")

    def __init__(self, pool, loader, rules_root):
        self._pool = pool
        self._loader = loader
        self._rules_root = rules_root

    def process_request(self):
        """
            GET  -- Returns a current version of the rules in format:
                    # =====
                    {
                        "head":    "<version>"
                        "errors":  {"<path.to.module>": "<Traceback>", ...}
                        "exposed": {
                            "methods":  ["<path.to.function>", ...],
                            "handlers": ["<path.to.function>", ...],
                        },
                    }
                    # =====
                    @head    -- Current version of the rules. Null if the version has not yet been set.
                    @errors  -- Errors that occurred while loading the specified modules.
                    @exposed -- Functions loaded from the rules and ready for execution.
                    @exposed.methods  -- List of functions that can be called directly by name.
                    @exposed.handlers -- List of event handlers that are selected based on filters.
                                         They may also be called manually as methods.

            POST -- Takes a version in the format: {"head": "<version>"}, applies it and returns
                    the result of the load process, in the same format as GET.

            Errors:
                    400 -- On error while loading the rules.
        """

        with self._pool.get_backend() as backend:
            if request.method == "POST":
                head = (request.data or {}).get("head")  # json
                try:
                    head = valid_hex_string(head)
                except ValidatorError as err:
                    raise ApiError(400, str(err), head=head)
                backend.rules.set_head(head)

            (head, exposed, errors, exc) = tools.get_exposed(backend, self._loader, self._rules_root)
            if exc is None:  # No errors
                if exposed is not None:
                    exposed_names = {group: list(methods) for (group, methods) in exposed.items()}
                else:
                    exposed_names = None  # Not configured HEAD
                return {"head": head, "exposed": exposed_names, "errors": errors}
            else:
                raise ApiError(400, exc, head=head)
