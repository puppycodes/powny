import abc

import flask


# =====
class ApiError(Exception):
    def __init__(self, code, message, **extra):
        super(ApiError, self).__init__()
        self.code = code
        self.message = message
        self.extra = extra


class Resource(metaclass=abc.ABCMeta):
    methods = ("GET",)

    def handler(self, **kwargs):
        try:
            return self.process_request(**kwargs)
        except ApiError as err:
            result = {"message": err.message}
            result.update(err.extra)
            return (result, err.code)

    @abc.abstractmethod
    def process_request(self, **kwargs):
        raise NotImplementedError


def get_url_for(resource_class, **kwargs):
    return flask.request.host_url.rstrip("/") + flask.url_for(resource_class.name, **kwargs)
