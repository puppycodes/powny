import sys
import os
import re
import importlib
import traceback
import threading

from contextlog import get_logger


# =====
_ATTR_EXPOSED = "_powny_exposed"


# =====
def expose(method):
    setattr(method, _ATTR_EXPOSED, True)
    return method


class Loader:
    """
        Loader() обеспечивает загрузку и перезагрузку пакета с правилами.
        При вызове get_exposed(), он удаляет все модули, __file__ которых начинается с prefix.
        Затем, в sys.path добавлется prefix/head и происходит загрузка всех пакетов и модулей
        из этого каталога, рекурсивно.
        Далее загружаются все фунции с декоратором @expose из этих модулей.
        Операция замены модулей не является атомарной и функции, которые во время обновления
        модулей обратились к оным, потерпят сбой. FIXME: исправить это.
    """

    _lock = threading.Lock()

    def __init__(self, prefix):
        self._prefix = prefix
        self._cache = {}
        self._thread = None

    def get_exposed(self, head):
        while True:
            if head in self._cache:
                return self._cache[head]

            if not self._lock.acquire(blocking=False):
                self._lock.acquire()
                self._lock.release()
                continue

            self._thread = threading.current_thread()
            try:
                _remove_modules_unsafe(self._prefix)
                (exposed_methods, errors) = _get_exposed_unsafe(os.path.join(self._prefix, head))
                self._cache[head] = (exposed_methods, errors)
                return self._cache[head]
            finally:
                self._thread = None
                self._lock.release()


# =====
def _remove_modules_unsafe(path):
    logger = get_logger()
    logger.debug("Removed modules with path: %s", path)

    for name in list(sys.modules):
        module_path = getattr(sys.modules[name], "__file__", None)
        if module_path is None:
            # FIXME: We don't support the namespaces yet
            logger.debug("Ignored module/package without __file__ attribute: %s", name)
        elif module_path.startswith(os.path.normpath(path) + os.path.sep):
            logger.debug("Removed old module: %s", name)
            del sys.modules[name]


def _get_exposed_unsafe(path):
    assert os.access(path, os.F_OK), "Can't find module path: {}".format(path)

    logger = get_logger()
    logger.debug("Loading scripts from path: %s", path)

    sys.path.insert(0, path)
    try:
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
            (_is_package, (lambda path: path), dirs),
            (_is_module, (lambda path: path[:-3]), files),
        ):
            for item in items:
                if _is_object_name(transformer(item)) and checker(os.path.join(root, item)):
                    obj_path = transformer(make_rel(root, item)).replace(os.path.sep, ".")
                    objects.append(obj_path)
    return sorted(objects)


def _is_package_root(base_path, package_path):
    """
        Проверяет, что переданный package_path на самом деле является пакетом,
        откусывая от его пути base_path:
            package_path = base_path + / + rel_package_path
    """

    rel_package_path = os.path.relpath(package_path, base_path)
    if rel_package_path == ".":
        return True
    path = base_path
    for part in rel_package_path.split(os.path.sep):
        if not _is_object_name(part):
            return False
        path = os.path.join(path, part)
        if not os.path.isfile(os.path.join(path, "__init__.py")):
            return False
    return True


def _is_object_name(name):
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))


def _is_package(path):
    if path.endswith("__pycache__"):
        return False
    return os.path.isfile(os.path.join(path, "__init__.py"))


def _is_module(path):
    return (os.path.basename(path) != "__init__.py" and path.endswith(".py"))
