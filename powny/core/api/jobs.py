from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_uuid

from ..backends import DeleteTimeoutError
from .. import tools

from . import get_url_for
from . import (
    Resource,
    ApiError,
)


# =====
class JobsResource(Resource):
    name = "Create and view jobs"
    methods = ("GET", "POST")
    docstring = """
        GET  -- Returns a dict of all jobs in the system:
                # =====
                {
                    {
                        "status":   "ok",
                        "message":  "<...>",
                        "<job_id>": {
                            "url": "<http://api/url/to/control/the/job>"},
                        },
                        ...
                }
                # =====

        POST -- Run method or handler. If the argument "method" is specified, will
                be running the specified method (requires the full path from the rules).
                If this argument is not specified, it will be found and run the
                appropriate handlers. The arguments passed to method/handler via request
                body (in dict format).

                Return value:
                # =====
                {
                    "status":  "ok",
                    "message": "<...>",
                    "result":  {
                        "<job_id>": {
                            "method": "<path.to.function>",
                            "url": "<http://api/url/to/control/the/job>"},
                        },
                        ...
                    },
                }
                # =====

                For explicit method call will be returnet only one job_id, for handlers
                will be returned several identifiers for the appropriate handlers.

                Possible POST errors (with status=="error"):
                    404 -- Method not found (for method call).
                    503 -- In the queue is more then N jobs.
                    503 -- No HEAD or exposed methods.
    """

    def __init__(self, pool, loader, rules_root, input_limit):
        self._pool = pool
        self._loader = loader
        self._rules_root = rules_root
        self._input_limit = input_limit

    def process_request(self):
        with self._pool.get_backend() as backend:
            if request.method == "GET":
                return self._request_get(backend)
            elif request.method == "POST":
                return self._request_post(backend)

    def _request_get(self, backend):
        result = {
            job_id: {"url": self._get_job_url(job_id)}  # TODO: Add "method" key
            for job_id in backend.jobs_control.get_jobs_list()
        }
        return (result, ("No jobs" if len(result) == 0 else "The list with all jobs"))

    def _request_post(self, backend):
        if backend.jobs_control.get_input_size() >= self._input_limit:
            raise ApiError(503, "In the queue is more then {} jobs".format(self._input_limit))

        (head, exposed) = self._get_exposed(backend)
        method_name = request.args.get("method", None)
        kwargs = dict(request.data or {})

        if method_name is not None:
            result = self._run_method(backend, method_name, kwargs, head, exposed)
            return (result, "Method was launched")
        else:
            result = self._run_handlers(backend, kwargs, head, exposed)
            return (result, ("No matching handler" if len(result) == 0 else "Handlers were launched"))

    def _get_exposed(self, backend):
        (head, exposed, _, _) = tools.get_exposed(backend, self._loader, self._rules_root)
        if exposed is None:
            raise ApiError(503, "No HEAD or exposed methods")
        return (head, exposed)

    def _run_method(self, backend, method_name, kwargs, head, exposed):
        state = tools.get_dumped_method(method_name, kwargs, exposed)  # Validation is not required
        if state is None:
            raise ApiError(404, "Method not found")
        job_id = backend.jobs_control.add_job(head, method_name, kwargs, state)
        return {job_id: {"method": method_name, "url": self._get_job_url(job_id)}}

    def _run_handlers(self, backend, kwargs, head, exposed):
        jobs = {}
        for (handler_name, state) in tools.get_dumped_handlers(kwargs, exposed).items():
            job_id = backend.jobs_control.add_job(head, handler_name, kwargs, state)
            jobs[job_id] = {"method": handler_name, "url": self._get_job_url(job_id)}
        return jobs

    def _get_job_url(self, job_id):
        return get_url_for(JobControlResource, job_id=job_id)


class JobControlResource(Resource):
    name = "View and stop job"
    methods = ("GET", "DELETE")
    dynamic = True
    docstring = """
        GET    -- Returns the job state:
                  # =====
                  {
                      "status":  "ok",
                      "message": "<...>",
                      "result":  {
                          "method":   "<path.to.function>",  # Full method path in the rules
                          "version":  "<HEAD>",    # HEAD of the rules for this job
                          "kwargs":   {...},       # Function arguments
                          "number":   <int>,       # The serial number of the job
                          "created":  <str>,       # ISO-8601-like time when the job was created
                          "locked":   <bool>,      # Job in progress
                          "deleted":  <bool>,      # Job is waiting for a forced stop and delete
                          "taken":    <str|null>,  # ISO-8601-like time when job was started (taken from queue)
                          "finished": <str|null>,  # ISO-8601-like time when job was finished
                          "stack":    [...],       # Stack snapshot on last checkpoint
                          "retval":   <any|null>,  # Return value if finished and not failed
                          "exc":      <str|null>,  # Text exception if job was failed
                      },
                  }
                  # =====

        DELETE -- Request to immediate stop and remove the job. Waits until the collector does
                  not remove the job.

                  Return value:
                  # =====
                  {
                      "status":  "ok",
                      "message": "<...>",
                      "result": {"deleted": "<job_id>"},
                  }
                  # =====

                  Possible DELETE errors (with status=="error"):
                      503 -- The collector did not have time to remove the job, try again.

        Errors (with status=="error"):
            400 -- Invalid job id.
            404 -- Job not found (or DELETED).
    """

    def __init__(self, pool, delete_timeout):
        self._pool = pool
        self._delete_timeout = delete_timeout

    def process_request(self, job_id):  # pylint: disable=arguments-differ
        with self._pool.get_backend() as backend:
            if request.method == "GET":
                return self._request_get(backend, job_id)
            elif request.method == "DELETE":
                return self._request_delete(backend, job_id)

    def _request_get(self, backend, job_id):
        try:
            job_id = valid_uuid(job_id)
        except ValidatorError as err:
            raise ApiError(400, str(err))
        job_info = backend.jobs_control.get_job_info(job_id)
        if job_info is None:
            raise ApiError(404, "Job not found")
        return (job_info, "Information about the job")

    def _request_delete(self, backend, job_id):
        try:
            deleted = backend.jobs_control.delete_job(job_id, timeout=self._delete_timeout)
        except DeleteTimeoutError as err:
            raise ApiError(503, str(err))
        if not deleted:
            raise ApiError(404, "Job not found")
        else:
            return ({"deleted": job_id}, "The job has been removed")
