import socket
import urllib.request
import urllib.error
import json
import pprint
import logging

from . import const


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Exceptions #####
class ApiError(Exception):
    def __init__(self, name, text):
        super(ApiError, self).__init__()
        self._name = name
        self._text = text

    def get_name(self):
        return self._name

    def get_text(self):
        return self._text

    def __str__(self):
        return "%s: %s" % (self._name, self._text)


##### Public classes #####
class Proxy:
    def __init__(self, url, opener=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT): # pylint: disable=W0212
        self._url = url
        self._opener = ( opener or urllib.request.build_opener() )
        self._timeout = timeout
        self._inspect_cache = {}

    def __getattr__(self, name):
        return _Object(self, name)

    def __call__(self, path, *args, **kwargs):
        inspected_args = self._inspect_args(path)
        body_attrs = dict(zip(inspected_args, args))
        body_attrs.update(kwargs)

        request = urllib.request.Request(
            "%s/%s" % (self._url, path),
            json.dumps(body_attrs).encode(),
            { "Content-Type": "application/json" },
        )
        _logger.debug("RPC call to %s/%s(%s, %s)", self._url, path, args, kwargs)
        result = self._api_request(request)

        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("... ->\n%s", pprint.pformat(result))
        return result

    def _inspect_args(self, path):
        if path in self._inspect_cache:
            _logger.debug("Introspection data for method \"%s\" has been found in the cache", path)
            return self._inspect_cache[path]

        request = urllib.request.Request("%s/%s?action=%s" % (self._url, path, const.ACTION.INSPECT))
        _logger.debug("Getting information about the method \"%s\"...", path)
        args = self._api_request(request)[const.ARGS_ALL]
        self._inspect_cache[path] = args

        _logger.debug("Received introspection:")
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(pprint.pformat(args))
        return args

    def _api_request(self, request):
        try:
            response = self._opener.open(request, timeout=self._timeout)
        except urllib.error.HTTPError as err:
            result = json.loads(err.read().decode())
            raise ApiError(*result[const.API_EXCEPTION])
        result = json.loads(response.read().decode())
        return result[const.API_RETVAL]


##### Private classes #####
class _Object:
    def __init__(self, proxy, path):
        self._proxy = proxy
        self._path = path

    def __getattr__(self, name):
        return _Object(self._proxy, "%s/%s" % (self._path, name))

    def __call__(self, *args, **kwargs):
        return self._proxy(self._path, *args, **kwargs)

