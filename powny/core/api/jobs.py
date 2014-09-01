from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_uuid

from ..backends import DeleteTimeoutError
from .. import tools

from . import get_url_for
from . import make_error


# =====
class JobsResource:
    name = "Create and view jobs"
    methods = ("GET", "POST")

    def __init__(self, pool, loader, rules_root, input_limit):
        self._pool = pool
        self._loader = loader
        self._rules_root = rules_root
        self._input_limit = input_limit

    def handler(self):
        """
            foobar
        """

        with self._pool.get_backend() as backend:
            if request.method == "GET":
                return {
                    job_id: {"url": get_url_for(JobControlResource, job_id=job_id)}
                    for job_id in backend.jobs.control.get_jobs_list()
                }

            elif request.method == "POST":
                if backend.jobs.control.get_input_size() >= self._input_limit:
                    return make_error(503, "In the queue is more then {} jobs".format(self._input_limit))

                (head, exposed, _, _) = tools.get_exposed(backend, self._loader, self._rules_root)
                if exposed is None:
                    return make_error(503, "No HEAD or exposed methods")
                method_name = request.args.get("method", None)
                func_kwargs = dict(request.data or {})

                if method_name is not None:  # XXX: Method
                    func = tools.get_func_method(method_name, exposed)  # Validation is not required
                    if func is None:
                        return make_error(503, "Unknown method")
                    job_id = backend.jobs.control.add_job(head, method_name, func, func_kwargs)
                    return {job_id: method_name}

                else:  # XXX: Event handlers
                    return {
                        backend.jobs.control.add_job(head, handler_name, func, func_kwargs): handler_name
                        for (handler_name, func) in tools.get_func_handlers(func_kwargs, exposed).items()
                    }


class JobControlResource:
    name = "View and stop job"
    methods = ("GET", "DELETE")
    dynamic = True

    def __init__(self, pool, delete_timeout):
        self._pool = pool
        self._delete_timeout = delete_timeout

    def handler(self, job_id):
        """
            foobar
        """

        with self._pool.get_backend() as backend:
            if request.method == "GET":
                try:
                    job_id = valid_uuid(job_id)
                except ValidatorError as err:
                    return make_error(400, str(err))
                job_info = backend.jobs.control.get_job_info(job_id)
                if job_info is None:
                    return make_error(404, "Job not found")
                return job_info

            elif request.method == "DELETE":
                try:
                    deleted = backend.jobs.control.delete_job(job_id, timeout=self._delete_timeout)
                except DeleteTimeoutError as err:
                    return make_error(503, str(err))
                if not deleted:
                    return make_error(404, "Job not found")
                else:
                    return {"deleted": job_id}
