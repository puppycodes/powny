from flask import request

from ..tools import get_exposed
from ..tools import make_job_state

from ..golem import check_match
from ..golem import convert_golem_event
from ..golem import IncorrectEventError

from . import get_url_for
from . import Resource
from . import ApiError

from .jobs import JobControlResource


# =====
class GolemResource(Resource):
    name = "Push Golem event"
    methods = ("GET", "POST")
    docstring = "Golem-compat handle"

    def __init__(self, pool, loader, input_limit):
        self._pool = pool
        self._loader = loader
        self._input_limit = input_limit

    def process_request(self):
        try:
            current = convert_golem_event(self._get_event_data())
        except IncorrectEventError as err:
            raise ApiError(400, str(err))

        with self._pool.get_backend() as backend:
            if backend.jobs_control.get_input_size() >= self._input_limit:
                raise ApiError(503, "In the queue is more then {} jobs".format(self._input_limit))
            previous = self._get_previous_and_replace(backend, current)
            (head, exposed) = self._get_exposed(backend)
            result = self._run_handlers(backend, previous, current, head, exposed)
            return (result, ("No matching handler" if len(result) == 0 else "Handlers were launched"))

    def _run_handlers(self, backend, previous, current, head, exposed):
        jobs = self._make_jobs_by_matchers(head, previous, current, exposed)
        if len(jobs) == 0:
            return {}
        else:
            return {
                job_id: {"method": job.method_name, "url": self._get_job_url(job_id)}
                for (job_id, job) in zip(backend.jobs_control.add_jobs(head, jobs), jobs)
            }

    def _get_job_url(self, job_id):
        return get_url_for(JobControlResource, job_id=job_id)

    def _get_event_data(self):
        data = dict(request.args)
        if request.method == "POST":
            data.update(dict(request.data or {}))
        for (key, value) in data.items():
            data[key] = (value[-1] if isinstance(value, (list, tuple)) else value)
        return data

    def _get_exposed(self, backend):
        (head, exposed, _, _) = get_exposed(backend, self._loader)
        if exposed is None:
            raise ApiError(503, "No HEAD or exposed methods")
        return (head, exposed)

    def _get_previous_and_replace(self, backend, current):
        old = backend.cas_storage.replace_value(
            path="__check_state/{}/{}".format(current["host"], current["service"]),
            value=current,
            default=None,
        )[0]
        return old.value

    def _make_jobs_by_matchers(self, head, previous, current, exposed):
        return [
            make_job_state(head, name, method, {"previous": previous, "current": current})
            for (name, method) in exposed.get("handlers", {}).items()
            if check_match(method, previous, current)
        ]
