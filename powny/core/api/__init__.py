import flask


# =====
def get_url_for(resource_class, **kwargs):
    return flask.request.host_url.rstrip("/") + flask.url_for(resource_class.name, **kwargs)


def make_error(code, message, **extra):
    result = {"message": message}
    result.update(extra)
    return (result, code)
