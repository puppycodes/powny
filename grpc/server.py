import sys
import cherrypy
import types
import inspect
import json
import pkgutil
import mako.template
import textwrap
import logging

from . import const


##### Private constants #####
_API_METHOD = "_api_method"

_TEMPLATE_MODULE = ("grpc", "templates/module.html")
_TEMPLATE_METHOD = ("grpc", "templates/method.html")


##### Private objects #####
_logger = logging.getLogger(const.LOGGER_NAME)


##### Public methods #####
def api(method):
    @cherrypy.expose
    @cherrypy.tools.allow(methods=("GET", "POST"))
    def wrap(self, action = None):
        if cherrypy.request.method == "GET":
            if action is None or action == const.ACTION.INFO:
                return _api_info(method)
            elif action == const.ACTION.INSPECT:
                return _api_inspect(method)
            else:
                raise cherrypy.HTTPError(400, "Invalid action")
        else: # POST
            if action is not None:
                raise cherrypy.HTTPError(400, "Invalid action")
            return _api_invoke(self, method)
    setattr(wrap, _API_METHOD, None)
    return wrap


##### Public classess #####
def _error_page(status, message, traceback, version):
    (err, text) = sys.exc_info()[:2]
    return json.dumps({
            const.API_EXCEPTION: (err.__name__, str(text)),
        })

class Module:
    _cp_config = {
        "error_page.default": _error_page,
    }

    @cherrypy.expose
    def index(self):
        modules_list = []
        methods_list = []
        for name in dir(self):
            item = getattr(self, name)
            if isinstance(item, Module):
                modules_list.append(name)
            elif isinstance(item, types.MethodType):
                if name == "index" or not hasattr(item, _API_METHOD):
                    continue
                methods_list.append(name)
        return _render_template(
            _TEMPLATE_MODULE,
            url=cherrypy.url(),
            modules_list=modules_list,
            methods_list=methods_list,
        ).encode()


##### Private methods #####
def _api_info(method):
    (required_list, optional_dict, _, variable_flag) = _inspect_args(method)
    return _render_template(
        _TEMPLATE_METHOD,
        url=cherrypy.url(),
        doc=textwrap.dedent(method.__doc__ or ""),
        required_list=required_list,
        optional_dict=optional_dict,
        variable_flag=variable_flag,
    ).encode()

def _api_inspect(method):
    (required_list, optional_dict, all_list, variable_flag) = _inspect_args(method)
    cherrypy.response.headers["Content-Type"] = "application/json"
    return json.dumps({
            const.ARGS_REQUIRED: required_list,
            const.ARGS_OPTIONAL: optional_dict,
            const.ARGS_ALL:      all_list,
            const.ARGS_VARIABLE: variable_flag,
        }).encode()

def _api_invoke(obj, method):
    cl = int(cherrypy.request.headers["Content-Length"])
    args_dict = json.loads(cherrypy.request.body.read(cl).decode())
    args_dict["self"] = obj
    cherrypy.response.headers["Content-Type"] = "application/json"
    return json.dumps({
            const.API_RETVAL: _invoke(method, args_dict),
        }).encode()

###
def _inspect_args(method):
    args_spec = inspect.getargspec(method)
    if args_spec.defaults is None or len(args_spec.defaults) == 0:
        required_list = args_spec.args
        optional_dict = {}
    else:
        required_list = args_spec.args[:-len(args_spec.defaults)]
        optional_dict = dict(zip(args_spec.args[len(args_spec.defaults)+1:], args_spec.defaults))
    required_list.remove("self")
    return (required_list, optional_dict, args_spec.args, ( args_spec.keywords is not None ))

def _invoke(method, args_dict):
    required_list = _inspect_args(method)[0]
    missing_list = list(set(required_list).difference(args_dict))
    if len(missing_list) != 0:
        message = "Missing required arguments: %s" % (", ".join(missing_list))
        _logger.error(message)
        raise cherrypy.HTTPError(400, message)

    _logger.info("HTTP call: %s.%s(%s)", method.__module__, method.__name__, args_dict)
    return method(**args_dict)

def _render_template(template_tuple, **kwargs_dict):
    return mako.template.Template(pkgutil.get_data(*template_tuple)).render(**kwargs_dict)

