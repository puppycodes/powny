import os
import threading
import time

from contextlog import get_logger

from ...core.backends import (
    DeleteTimeoutError,
    JobState,
    make_job_id,
    CasNoValueError,
    CasVersionError,
    CasNoValue,
    CasData,
)
from ...core.tools import (
    make_isotime,
    from_isotime,
    get_node_name,
)

from . import zoo


# =====
_PATH_INPUT_QUEUE = "/input_queue"
_PATH_SYSTEM = "/system"
_PATH_RULES_HEAD = zoo.join(_PATH_SYSTEM, "rules_head")
_PATH_APPS_STATE = zoo.join(_PATH_SYSTEM, "apps_state")
_PATH_JOBS = "/jobs"
_PATH_USER = "/user"
_PATH_CAS_STORAGE = zoo.join(_PATH_USER, "cas_storage")


def _get_path_job(job_id):
    return zoo.join(_PATH_JOBS, job_id)


def _get_path_job_lock(job_id):
    return zoo.join(_get_path_job(job_id), "lock")


def _get_path_job_taken(job_id):
    return zoo.join(_get_path_job(job_id), "taken")


def _get_path_job_state(job_id):
    return zoo.join(_get_path_job(job_id), "state")


def _get_path_job_delete(job_id):
    return zoo.join(_get_path_job(job_id), "delete")


def _get_path_app_state(app_name, node_name):
    return zoo.join(_PATH_APPS_STATE, "{}@{}".format(app_name, node_name))


def _parse_app_state_node(node_name):
    return tuple(node_name.split("@"))


def _get_path_cas_storage(path):
    return zoo.join(_PATH_CAS_STORAGE, path)


def _get_path_cas_storage_lock(path):
    return zoo.join(_get_path_cas_storage(path), "__lock__")


def _make_lock_info(label):
    return {
        "from":     label,
        "when":     make_isotime(),
        "instance": {
            "node": get_node_name(),
            "pid": os.getpid(),
        },
    }


# =====
def init(client):
    logger = get_logger()
    for path in (
        _PATH_INPUT_QUEUE,
        _PATH_SYSTEM,
        _PATH_RULES_HEAD,
        _PATH_APPS_STATE,
        _PATH_JOBS,
        _PATH_USER,
        _PATH_CAS_STORAGE,
    ):
        try:
            with client.make_write_request("backend::init()::create({})".format(path)) as request:
                request.create(path)
            logger.debug("Backend init: path '%s' has been created", path)
        except zoo.NodeExistsError:
            logger.debug("Backend init: path '%s' is already exists", path)


# =====
class JobsControl:
    """
        Interface to managing the jobs (add, delete, get metadata).
        Needs for powny.core.apps.api.
    """

    def __init__(self, client):
        self._client = client
        self._input_queue = self._client.get_queue(_PATH_INPUT_QUEUE)

    def get_jobs_list(self):
        return self._client.get_children(_PATH_JOBS)

    def get_input_size(self):
        return len(self._input_queue)

    def get_jobs_count(self):
        return self._client.get_children_count(_PATH_JOBS)

    def add_jobs(self, head, jobs):
        now = make_isotime()
        added_ids = []
        with self._client.make_write_request("add_jobs()") as request:
            for job in jobs:
                job_id = make_job_id()
                get_logger().info("Registering job", job_id=job_id, head=head,
                                  method=job.method_name, kwargs=job.kwargs)
                request.create(_get_path_job(job_id), {
                    "head": head,
                    "method": job.method_name,
                    "kwargs": job.kwargs,
                    "created": now,
                })
                request.create(_get_path_job_state(job_id), {
                    "state": job.state,
                    "stack": None,
                    "finished": None,
                    "retval": None,
                    "exc": None,
                })
                self._input_queue.put(request, job_id)
                added_ids.append(job_id)
        return added_ids

    def delete_job(self, job_id, timeout=None):
        logger = get_logger(job_id=job_id)
        logger.info("Deleting job")
        try:
            with self._client.make_write_request("delete_job()") as request:
                request.create(_get_path_job_delete(job_id), make_isotime())
        except zoo.NodeExistsError:
            pass  # Lock on existent delete-op
        except zoo.NoNodeError:
            return False
        wait = threading.Event()
        if self._client.exists(_get_path_job_delete(job_id), watch=lambda _: wait.set()):
            wait.wait(timeout=timeout)
            if not wait.is_set():
                msg = "The job was not removed, try again"
                logger.error(msg)
                raise DeleteTimeoutError(msg)
        logger.info("Deleted job")
        return True

    def get_job_info(self, job_id):
        try:
            job_info = self._client.get(_get_path_job(job_id))  # init info

            job_info["deleted"] = self._client.get(_get_path_job_delete(job_id), None)
            job_info["locked"] = self._client.get(_get_path_job_lock(job_id), None)
            job_info["taken"] = self._client.get(_get_path_job_taken(job_id), None)

            state_info = self._client.get(_get_path_job_state(job_id))
            state_info.pop("state", None)  # Remove state
            job_info["finished"] = state_info.pop("finished")
            job_info.update(state_info)  # + stack OR retval OR exc

            return job_info
        except zoo.NoNodeError:
            return None


class JobsProcess:
    """
        Interface to processing the jobs.
        Needs for powny.core.apps.worker.
    """

    def __init__(self, client):
        self._client = client
        self._input_queue = self._client.get_queue(_PATH_INPUT_QUEUE)

    def get_ready_jobs(self):
        for job_id in self._input_queue:
            job_info = self._client.get(_get_path_job(job_id))
            exec_info = self._client.get(_get_path_job_state(job_id))

            with self._client.make_write_request("get_ready_jobs()") as request:
                lock = self._client.get_lock(_get_path_job_lock(job_id))
                lock.acquire(request, _make_lock_info("get_ready_jobs()"))
                request.create(_get_path_job_taken(job_id), make_isotime())
                self._input_queue.consume(request)

            yield JobState(
                head=job_info["head"],
                method_name=job_info["method"],
                kwargs=job_info["kwargs"],
                state=exec_info["state"],
                job_id=job_id,
            )

    def associate_job(self, job_id):
        with self._client.make_write_request("associate_job()") as request:
            # Assign lock to current process
            lock = self._client.get_lock(_get_path_job_lock(job_id))
            lock.release(request)
            lock.acquire(request, _make_lock_info("associate_job()"))

    def release_job(self, job_id):
        with self._client.make_write_request("release_job()") as request:
            self._client.get_lock(_get_path_job_lock(job_id)).release(request)

    def is_deleted_job(self, job_id):
        return self._client.exists(_get_path_job_delete(job_id))

    def save_job_state(self, job_id, state, stack):
        with self._client.make_write_request("save_job_state()") as request:
            request.set(_get_path_job_state(job_id), {
                "state":    state,
                "stack":    stack,
                "finished": None,
                "retval":   None,
                "exc":      None,
            })

    def done_job(self, job_id, retval, exc):
        with self._client.make_write_request("done_job()") as request:
            request.set(_get_path_job_state(job_id), {
                "state":    None,
                "stack":    None,
                "finished": make_isotime(),
                "retval":   retval,
                "exc":      exc,
            })
            self._client.get_lock(_get_path_job_lock(job_id)).release(request)


class JobsGc:
    """
        Interface for garbage collector.
        Needs for powny.core.apps.collector.
    """

    def __init__(self, client):
        self._client = client
        self._input_queue = self._client.get_queue(_PATH_INPUT_QUEUE)

    def get_jobs(self, done_lifetime):
        for job_id in self._client.get_children(_PATH_JOBS):
            to_delete = self._client.exists(_get_path_job_delete(job_id))
            taken = self._client.exists(_get_path_job_taken(job_id))
            lock = self._client.get_lock(_get_path_job_lock(job_id))

            if (to_delete or taken) and not lock.is_locked():
                try:
                    finished = self._client.get(_get_path_job_state(job_id))["finished"]
                except zoo.NoNodeError:
                    continue
                if to_delete or finished is None or from_isotime(finished) + done_lifetime <= time.time():
                    try:
                        with self._client.make_write_request("get_unfinished_jobs()") as request:
                            lock.acquire(request, _make_lock_info("get_unfinished_jobs()"))
                    except (zoo.NoNodeError, zoo.NodeExistsError):
                        continue
                    yield (job_id, to_delete or finished is not None)  # (id, done)

    def push_back_job(self, job_id):
        with self._client.make_write_request("push_back_job()") as request:
            request.delete(_get_path_job_taken(job_id))
            request.delete(_get_path_job_lock(job_id))
            self._input_queue.put(request, job_id)

    def remove_job_data(self, job_id):
        with self._client.make_write_request("remove_job_data()") as request:
            for path_maker in (
                _get_path_job_delete,
                _get_path_job_taken,
            ):
                path = path_maker(job_id)
                if self._client.exists(path):
                    request.delete(path)
            request.delete(_get_path_job_lock(job_id))
            request.delete(_get_path_job_state(job_id))
            request.delete(_get_path_job(job_id))


class Rules:
    """
        Interface to managing the rules HEAD.
    """

    def __init__(self, client):
        self._client = client

    def set_head(self, head):
        with self._client.make_write_request("set_head()") as request:
            request.set(_PATH_RULES_HEAD, head)

    def get_head(self):
        head = self._client.get(_PATH_RULES_HEAD)
        if head is zoo.EmptyValue:
            return None
        else:
            return head


class AppsState:
    """
        Interface to the system statistics about the internal processes
        (like the worker and collector).
    """

    def __init__(self, client):
        self._client = client

    def set_state(self, app_name, app_state):
        state = {
            "when": make_isotime(),
            "pid": os.getpid(),
            "state": app_state,
        }
        self._set_raw_state(app_name, get_node_name(), state)

    def _set_raw_state(self, app_name, node_name, state):
        path = _get_path_app_state(app_name, node_name)
        try:
            with self._client.make_write_request("set_state()") as request:
                request.set(path, state)
        except zoo.NoNodeError:
            with self._client.make_write_request("create_state_node()") as request:
                request.create(path, state, ephemeral=True)

    def get_full_state(self):
        full_state = {}
        for app_state_node in self._client.get_children(_PATH_APPS_STATE):
            (app_name, node_name) = _parse_app_state_node(app_state_node)
            try:
                state = self._client.get(_get_path_app_state(app_name, node_name))
            except zoo.NoNodeError:
                continue
            full_state.setdefault(app_name, {})
            full_state[app_name][node_name] = state
        return full_state


class CasStorage:
    """
        Interface to abstract CAS storage for user scripts.
    """

    def __init__(self, client):
        self._client = client

    def set_value(self, path, value, version=None):
        try:
            self.replace_value(path, value=value, version=version, default=None)
            return True
        except CasVersionError:
            get_logger().exception("Can't set '%s' value with version %s", path, version)
            return False

    def get_value(self, path, default=CasNoValue):
        return self.replace_value(path, value=CasNoValue, default=default)[0]

    def replace_value(self, path, value=CasNoValue, version=None, default=CasNoValue, fatal_write=True):
        """
            replace_value() - implementation of the CAS, stores the new value if it is superior to the
                              existing version. Standard kazoo set() require strict comparison and
                              incremented version of the data themselves.

            If:
                value == CasNoValue -- read operation
                value == ... -- write the new value and return the old

                version is None -- write
                version is not None -- write if version >= old_version
        """

        path = _get_path_cas_storage(path)

        try:
            with self._client.make_write_request("cas_ensure_path()") as request:
                request.create(path, recursive=True)
        except zoo.NodeExistsError:
            pass

        with self._client.get_lock(_get_path_cas_storage_lock(path)):
            old = self._client.get(path)
            if old is zoo.EmptyValue:
                if default is CasNoValue:
                    raise CasNoValueError()
                old = CasData(value=default, version=None, stored=None)
            else:
                old = CasData(
                    value=old["value"],
                    version=old["version"],
                    stored=from_isotime(old["stored"]),
                )

            if value is not CasNoValue:
                if version is not None and old.version is not None and version <= old.version:
                    write_ok = False
                    msg = "Can't rewrite '{}' with version {} (old version: {})".format(path, version, old.version)
                    if fatal_write:
                        raise CasVersionError(msg)
                    else:
                        get_logger().debug(msg)
                else:
                    with self._client.make_write_request("cas_save()") as request:
                        request.set(path, {
                            "value":   value,
                            "version": version,
                            "stored":  make_isotime(),
                        })
                        write_ok = True
            else:
                write_ok = None

        return (old, write_ok)
