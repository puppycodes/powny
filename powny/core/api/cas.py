import os

from flask import request

from . import (
    valid_object_name,
    Resource,
    ApiError,
)


# =====
class CasPathResource(Resource):
    name = "View CAS data"
    dynamic = True
    docstring = """
        GET  -- Returns a dict with CAS user data:
                # =====
                {
                    "status":   "ok",
                    "message":  "<...>",
                    "result": {
                        "children": [
                            {"name": "<child>", "url": "http://api/url/to/child"},
                            ...
                        ],
                        "data": {
                            "stored": "<ISO-8601-like-time>",
                            "value": <any_type>,
                            "version": <int>|null,
                        }|null,
                    },
                }
                # =====

                Possible GET errors:
                    404 -- Non-existant CAS path.
    """

    def __init__(self, pool):
        self._pool = pool

    def process_request(self, path):  # pylint: disable=arguments-differ
        path = "/".join(map(valid_object_name, filter(None, path.split("/"))))
        path = "/" + path
        backend = self._pool.get_backend()
        try:
            children = backend.cas_storage.get_children(path)
            if children is None:
                raise ApiError(404, "Path not found")
            return ({
                "children": [
                    {"name": child, "url": os.path.join(request.base_url, child)}
                    for child in children
                ],
                "data": backend.cas_storage.get_raw(path),
            }, self.name)
        finally:
            self._pool.retrieve_backend(backend)


class CasRootResource(CasPathResource):
    dynamic = False

    def process_request(self):  # pylint: disable=arguments-differ
        return super().process_request("")
