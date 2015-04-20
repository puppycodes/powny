import uuid
import re

from flask import request

from ..backends import DeleteTimeoutError

from ..tools import get_exposed
from ..tools import make_job_state

from . import get_url_for
from . import Resource
from . import ApiError


# =====
def _valid_job_id(job_id):
    job_id = str(job_id).strip()
    if re.match(r"^[\w-]{1,100}$", job_id) is None:
        raise ApiError(400, "Invalid job id, required something like this: ^[\\w-]{1,100}$")
    return job_id


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
                    400 -- Missed required argument; job already exists.
                    404 -- Method not found (for method call).
                    503 -- No HEAD or exposed methods.
    """

    def __init__(self, pool, loader):
        self._pool = pool
        self._loader = loader

    def process_request(self):
        backend = self._pool.get_backend()
        try:
            if request.method == "GET":
                return self._request_get(backend)
            elif request.method == "POST":
                return self._request_post(backend)
        finally:
            self._pool.retrieve_backend(backend)

    def _request_get(self, backend):
        result = {
            job_id: {"url": self._get_job_url(job_id)}  # TODO: Add "method" key
            for job_id in backend.jobs_control.get_jobs_list()
        }
        return (result, ("No jobs" if len(result) == 0 else "The list with all jobs"))

    def _request_post(self, backend):
        (head, exposed) = self._get_exposed(backend)
        job_id = _valid_job_id(request.args.get("job_id", str(uuid.uuid4())))
        method_name = request.args.get("method", None)
        if method_name is None:
            raise ApiError(400, "Required method_name")
        kwargs = dict(request.data or {})

        result = self._run_method(backend, job_id, method_name, kwargs, head, exposed)
        return (result, "Method was launched")

    def _get_exposed(self, backend):
        (head, exposed, _, _) = get_exposed(backend, self._loader)
        if exposed is None:
            raise ApiError(503, "No HEAD or exposed methods")
        return (head, exposed)

    def _run_method(self, backend, job_id, method_name, kwargs, head, exposed):
        method = exposed.get("methods", {}).get(method_name)
        if method is None:
            raise ApiError(404, "Method not found")
        job = make_job_state(job_id, head, method_name, method, kwargs)
        if not backend.jobs_control.add_job(job):
            raise ApiError(400, "Job already exists")
        return {job_id: {"method": method_name, "url": self._get_job_url(job_id)}}

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
        job_id = _valid_job_id(job_id)
        backend = self._pool.get_backend()
        try:
            if request.method == "GET":
                return self._request_get(backend, job_id)
            elif request.method == "DELETE":
                return self._request_delete(backend, job_id)
        finally:
            self._pool.retrieve_backend(backend)

    def _request_get(self, backend, job_id):
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
