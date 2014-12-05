from flask import request

from ulib.validatorlib import ValidatorError
from ulib.validators.extra import valid_uuid

from ..backends import DeleteTimeoutError

from ..tools import get_exposed
from ..tools import make_job_state

from . import get_url_for
from . import Resource
from . import ApiError


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

        POST -- Run the specified method. If the argument "method" is specified, will
                be running the specified method (requires the full path from the rules).
                The arguments passed to method via request body (in dict format).

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
                    },
                }
                # =====

                Possible POST errors (with status=="error"):
                    404 -- Method not found (for method call).
                    503 -- In the queue is more then N jobs.
                    503 -- No HEAD or exposed methods.
    """

    def __init__(self, pool, loader, input_limit):
        self._pool = pool
        self._loader = loader
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
        if method_name is None:
            raise ApiError(400, "Requires method_name")
        kwargs = dict(request.data or {})

        result = self._run_method(backend, method_name, kwargs, head, exposed)
        return (result, "Method was launched")

    def _get_exposed(self, backend):
        (head, exposed, _, _) = get_exposed(backend, self._loader)
        if exposed is None:
            raise ApiError(503, "No HEAD or exposed methods")
        return (head, exposed)

    def _run_method(self, backend, method_name, kwargs, head, exposed):
        job = self._make_job(head, method_name, kwargs, exposed)  # Validation is not required
        if job is None:
            raise ApiError(404, "Method not found")
        job_id = backend.jobs_control.add_jobs(head, [job])[0]
        return {job_id: {"method": method_name, "url": self._get_job_url(job_id)}}

    def _make_job(self, head, name, kwargs, exposed):
        method = exposed.get("methods", {}).get(name)
        if method is None:
            return None
        else:
            return make_job_state(head, name, method, kwargs)

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
                          "head":     "<HEAD>",    # HEAD of the rules for this job
                          "kwargs":   {...},       # Function arguments
                          "created":  <str>,       # ISO-8601-like time when the job was created
                          "locked":   <dict|null>, # Job in progress (null if not locked, dict with info otherwise)
                          "deleted":  <str|null>,  # ISO-8601-like time when job was marked to stop and delete
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
