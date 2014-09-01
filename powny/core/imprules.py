import sys
import os
import importlib
import traceback
import threading
import collections

from contextlog import get_logger

from ulib.validatorlib import ValidatorError
from ulib.validators.python import valid_object_name


# =====
_ATTR_EXPOSED = "_powny_exposed"


# =====
def expose(method):
    setattr(method, _ATTR_EXPOSED, True)
    return method


class Loader:
    _lock = threading.Lock()

    def __init__(self, module_base, group_by=None):
        self.module_base = module_base
        self._group_by = group_by
        self._cache = {}
# FIXME
#        self._lock = threading.Lock()
        self.thread = None

    def get_exposed(self, path):
        while True:
            if path in self._cache:
                return self._cache[path]

            if not self._lock.acquire(blocking=False):
                self._lock.acquire()
                self._lock.release()
                continue

            self.thread = threading.current_thread()
            try:
                (exposed_methods, errors) = _get_exposed_unsafe(self.module_base, path)
                if self._group_by is None:
                    self._cache[path] = (exposed_methods, errors)
                else:
                    methods = {}
                    for (name, method) in exposed_methods.items():
                        for (sub, test) in self._group_by:
                            if test(method):
                                methods.setdefault(sub, {})
                                methods[sub][name] = method
                                break
                    self._cache[path] = (methods, errors)
                return self._cache[path]
            finally:
                self.thread = None
                self._lock.release()


def setup_hooks():
    pass
# FIXME
#    assert not isinstance(sys.path, _SysPath), "Double-called setup_hooks()"
#    assert not isinstance(sys.modules, _SysModules), "Double-called setup_hooks()"
#    sys.path = _SysPath()
#    sys.modules = _SysModules()

def remove_hooks():
    pass
#    assert isinstance(sys.path, _SysPath), "setup_hooks() was not called"
#    assert isinstance(sys.modules, _SysModules), "setup_hooks() was not called"
#    sys.path = sys.path.orig
#    sys.modules = sys.modules.orig


# =====
class _SysPath(collections.UserList):
    def __init__(self):  # pylint: disable=W0231
        self.orig = sys.path
        self._local = threading.local()

    @property
    def data(self):
        if not hasattr(self._local, "data"):
            self._local.data = list(self.orig)
        return self._local.data

class _SysModules(collections.UserDict):
    def __init__(self):  # pylint: disable=W0231
        self.orig = sys.modules
        self._local = threading.local()

    @property
    def data(self):
        if not hasattr(self._local, "data"):
            self._local.data = dict(self.orig)
        return self._local.data


# =====
def _get_exposed_unsafe(module_base, path):
    assert os.access(path, os.F_OK), "Can't find module path: {}".format(path)
    logger = get_logger()
    logger.debug("Loading rules from path: %s; root: %s", path, module_base)

    sys.path.insert(0, path)
    try:
        for name in list(sys.modules):
            if name == module_base or name.startswith(module_base + "."):
                logger.debug("Removed old module: %s", name)
                del sys.modules[name]

        modules = {}
        errors = {}
        for name in _get_all_modules(path):
            try:
                modules[name] = importlib.import_module(name)
            except Exception:
                errors[name] = traceback.format_exc()
                logger.exception("Can't import module '%s' from path '%s'", name, path)
        logger.debug("Found %d modules in path '%s'", len(modules), path)

        methods = {}
        for (module_name, module) in modules.items():
            for obj_name in dir(module):
                if obj_name.startswith("__"):
                    continue
                obj = getattr(module, obj_name)
                if callable(obj) and getattr(obj, _ATTR_EXPOSED, False):
                    methods["{}.{}".format(module_name, obj_name)] = obj
        logger.debug("Loaded %d exposed methods from path '%s'", len(methods), path)
        return (methods, errors)
    finally:
        sys.path.remove(path)

def _get_all_modules(base_path):
    base_path = os.path.abspath(base_path)
    make_rel = (lambda root, item: os.path.relpath(os.path.join(root, item), base_path))
    objects = []
    for (root, dirs, files) in os.walk(base_path, followlinks=True):
        if not _is_package_root(base_path, root):
            continue
        for (checker, transformer, items) in (
            (_is_package, lambda path: path, dirs),
            (_is_module,  lambda path: path[:-3], files),
        ):
            for item in items:
                if _is_object_name(transformer(item)) and checker(os.path.join(root, item)):
                    obj_path = transformer(make_rel(root, item)).replace(os.path.sep, ".")
                    objects.append(obj_path)
    return sorted(objects)

def _is_package_root(base_path, root):
    root = os.path.relpath(root, base_path)
    if root == ".":
        return True
    path = base_path
    for part in root.split(os.path.sep):
        if not _is_object_name(part):
            return False
        path = os.path.join(path, part)
        if not os.path.isfile(os.path.join(path, "__init__.py")):
            return False
    return True

def _is_object_name(name):
    try:
        valid_object_name(name)
        return True
    except ValidatorError:
        return False

def _is_package(path):
    if path.endswith("__pycache__"):
        return False
    return os.path.isfile(os.path.join(path, "__init__.py"))

def _is_module(path):
    return (os.path.basename(path) != "__init__.py" and path.endswith(".py"))
