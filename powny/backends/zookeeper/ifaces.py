import threading
import time

from contextlog import get_logger

from ...core.backends import DeleteTimeoutError
from ...core.backends import ReadyJob
from ...core.backends import make_job_id

from . import zoo


# =====
_PATH_INPUT_QUEUE = "/input_queue"
_PATH_SYSTEM = "/system"
_PATH_JOBS_COUNTER = zoo.join(_PATH_SYSTEM, "jobs_counter")
_PATH_RULES_HEAD = zoo.join(_PATH_SYSTEM, "rules_head")
_PATH_APPS_STATE = zoo.join(_PATH_SYSTEM, "apps_state")
_PATH_JOBS = "/jobs"


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

def _get_path_app_state(node_name, app_name):
    return zoo.join(_PATH_APPS_STATE, "{}@{}".format(app_name, node_name))

def _parse_app_state_node(node_name):
    return tuple(reversed(node_name.split("@")))


# =====
def init(client):
    logger = get_logger()
    for path in (
        _PATH_INPUT_QUEUE,
        _PATH_SYSTEM,
        _PATH_JOBS_COUNTER,
        _PATH_RULES_HEAD,
        _PATH_APPS_STATE,
        _PATH_JOBS,
    ):
        try:
            with client.get_write_request("backend::init()::create({})".format(path)) as request:
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
        self._jobs_counter = self._client.get_counter(_PATH_JOBS_COUNTER)

    def get_jobs_list(self):
        return self._client.get_children(_PATH_JOBS)

    def get_input_size(self):
        return len(self._input_queue)

    def get_jobs_count(self):
        return self._client.get_children_count(_PATH_JOBS)

    def add_job(self, version, method_name, kwargs, state):
        job_id = make_job_id()
        number = self._jobs_counter.increment()
        logger = get_logger(job_id=job_id, number=number, method=method_name)
        logger.info("Registering job")
        with self._client.get_write_request("add_job()") as request:
            request.create(_get_path_job(job_id), {
                "version": version,
                "method":    method_name,
                "kwargs":  kwargs,
                "created": time.time(),
                "number":  number,
            })
            request.create(_get_path_job_state(job_id), {
                "state":    state,
                "stack":    None,
                "finished": None,
                "retval":   None,
                "exc":      None,
            })
            self._input_queue.put(request, job_id)
        logger.info("Registered job")
        return job_id

    def delete_job(self, job_id, timeout=None):
        logger = get_logger(job_id=job_id)
        logger.info("Deleting job")
        try:
            with self._client.get_write_request("delete_job()") as request:
                request.create(_get_path_job_delete(job_id))
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
        get_logger(job_id=job_id).info("Deleted job")
        return True

    def get_job_info(self, job_id):
        try:
            job_info = self._client.get(_get_path_job(job_id))  # init info

            job_info["deleted"] = self._client.exists(_get_path_job_delete(job_id))
            job_info["locked"] = self._client.exists(_get_path_job_lock(job_id))
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

            with self._client.get_write_request("get_ready_jobs()") as request:
                self._client.get_lock(_get_path_job_lock(job_id)).acquire(request)
                request.create(_get_path_job_taken(job_id), time.time())
                self._input_queue.consume(request)

            yield ReadyJob(
                job_id=job_id,
                number=job_info["number"],
                version=job_info["version"],
                state=exec_info["state"],
            )

    def associate_job(self, job_id):
        with self._client.get_write_request("associate_job()") as request:
            # Assign lock to current process
            lock = self._client.get_lock(_get_path_job_lock(job_id))
            lock.release(request)
            lock.acquire(request)

    def is_deleted_job(self, job_id):
        return self._client.exists(_get_path_job_delete(job_id))

    def save_job_state(self, job_id, state, stack):
        with self._client.get_write_request("save_job_state()") as request:
            request.set(_get_path_job_state(job_id), {
                "state":    state,
                "stack":    stack,
                "finished": None,
                "retval":   None,
                "exc":      None,
            })

    def done_job(self, job_id, retval, exc):
        with self._client.get_write_request("done_job()") as request:
            request.set(_get_path_job_state(job_id), {
                "state":    None,
                "stack":    None,
                "finished": time.time(),
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
                finished = self._client.get(_get_path_job_state(job_id))["finished"]
                if to_delete or finished is None or finished + done_lifetime <= time.time():
                    try:
                        with self._client.get_write_request("get_unfinished_jobs()") as request:
                            lock.acquire(request)
                    except (zoo.NoNodeError, zoo.NodeExistsError):
                        continue
                    yield (job_id, to_delete or finished is not None)  # (id, done)

    def push_back_job(self, job_id):
        with self._client.get_write_request("push_back_job()") as request:
            request.delete(_get_path_job_taken(job_id))
            request.delete(_get_path_job_lock(job_id))
            self._input_queue.put(request, job_id)

    def remove_job_data(self, job_id):
        with self._client.get_write_request("remove_job_data()") as request:
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
        with self._client.get_write_request("set_head()") as request:
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

    def set_state(self, node_name, app_name, state):
        path = _get_path_app_state(node_name, app_name)
        try:
            with self._client.get_write_request("set_state()") as request:
                request.set(path, state)
        except zoo.NoNodeError:
            with self._client.get_write_request("create_state_node()") as request:
                request.create(path, ephemeral=True)
            self.set_state(node_name, app_name, state)

    def get_full_state(self):
        full_state = {}
        for app_state_node in self._client.get_children(_PATH_APPS_STATE):
            (node_name, app_name) = _parse_app_state_node(app_state_node)
            try:
                app_state = self._client.get(_get_path_app_state(node_name, app_name))
            except zoo.NoNodeError:
                continue
            full_state.setdefault(node_name, {})
            full_state[node_name][app_name] = app_state
        return full_state
