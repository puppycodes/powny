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
    methods = ("GET", "DELETE")
    dynamic = True
    docstring = """
        GET    -- Returns a dict with CAS user data:
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

        DELETE -- Remove node without children.
                  Possible DELETE errors:
                      400 -- Node not empty (has children).
                      404 -- Non-existant CAS path.
    """

    def __init__(self, pool):
        self._pool = pool

    def process_request(self, path):  # pylint: disable=arguments-differ
        path = "/".join(map(valid_object_name, filter(None, path.split("/"))))
        path = "/" + path
        backend = self._pool.get_backend()
        try:
            if request.method == "GET":
                return self._request_get(backend, path)
            elif request.method == "DELETE":
                return self._request_delete(backend, path)
        finally:
            self._pool.retrieve_backend(backend)

    def _request_get(self, backend, path):
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

    def _request_delete(self, backend, path):
        retval = backend.cas_storage.delete(path)
        if retval is None:
            raise ApiError(400, "Path has children")
        if not retval:
            raise ApiError(404, "Path not found")
        return (None, self.name)


class CasRootResource(CasPathResource):
    methods = ("GET",)
    dynamic = False

    def process_request(self):  # pylint: disable=arguments-differ
        return super().process_request("")
