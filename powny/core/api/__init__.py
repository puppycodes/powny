import re
import abc

from contextlog import get_logger

import flask


# =====
class ApiError(Exception):
    def __init__(self, code, message, result=None):
        super(ApiError, self).__init__()
        self.code = code
        self.message = message
        self.result = result


class Resource(metaclass=abc.ABCMeta):
    name = "<Resource>"
    dynamic = False
    methods = ("GET",)
    docstring = None

    def handler(self, **kwargs):
        try:
            (result, message) = self.process_request(**kwargs)
            return {
                "status": "ok",
                "message": message,
                "result": result
            }
        except ApiError as err:
            result = {
                "status": "error",
                "message": err.message,
                "result": err.result,
            }
            return (result, err.code)
        except Exception as err:
            get_logger().exception("Unhandled API exception")
            message = "{}: {}".format(type(err).__name__, err)
            if hasattr(err, "__module__"):
                message = "{}.{}".format(err.__module__, message)
            result = {
                "status": "error",
                "message": message,
                "result": None,
            }
            return (result, 500)

    @abc.abstractmethod
    def process_request(self, **kwargs):
        raise NotImplementedError


def valid_object_name(name):
    if re.match(r"^[\w-]{1,100}$", name) is None:
        raise ApiError(400, "Invalid object name, required something like this: ^[\\w-]{1,100}$")
    return name


def get_exposed(backend, loader):
    head = backend.scripts.get_head()
    exposed = None
    errors = None
    exc = None
    if head is not None:
        try:
            (exposed, errors) = loader.get_exposed(head)
        except Exception as err:
            exc = "{}: {}".format(type(err).__name__, err)
            get_logger().exception("Can't load HEAD '%s'", head)
    return (head, exposed, errors, exc)


def get_url_for(obj, **kwargs):
    if hasattr(obj, "__name__"):
        name = obj.__name__
    else:
        name = obj.__class__.__name__
    return flask.request.host_url.rstrip("/") + flask.url_for(name, **kwargs)
