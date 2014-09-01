from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_hex_string

from .. import tools

from . import make_error


# =====
class RulesResource:
    name = "Operations with the rules HEAD"
    methods = ("GET", "POST")

    def __init__(self, pool, loader, rules_root):
        self._pool = pool
        self._loader = loader
        self._rules_root = rules_root

    def handler(self):
        """
            TODO
            GET  -- Returns the current version of the rules in format {"head": "version"}.
                    If the version has not yet been set, returns null: {"head": null}.
            POST -- Takes the value of the version in the same format that is used in the GET,
                    applies it, and returns the new current version.
        """

        with self._pool.get_backend() as backend:
            if request.method == "POST":
                head = (request.data or {}).get("head")  # json
                try:
                    head = valid_hex_string(head)
                except ValidatorError as err:
                    return make_error(400, str(err), head=head)
                backend.rules.set_head(head)

            (head, exposed, errors, exc) = tools.get_exposed(backend, self._loader, self._rules_root)
            if exc is None:  # No errors
                if exposed is not None:
                    exposed_names = {group: list(methods) for (group, methods) in exposed.items()}
                else:
                    exposed_names = None  # Not configured HEAD
                return {"head": head, "exposed": exposed_names, "errors": errors}
            else:
                return make_error(400, exc, head=head)
