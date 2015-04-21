import collections
import uuid

from contextlog import get_logger

from ..core import context


# =====
def run_in_context(method, kwargs=None, job_id=None, extra=None, fatal=True):
    if callable(method):
        state = context.dump_call(method, (kwargs or {}))
    else:
        assert isinstance(method, bytes)
        state = method

    backend = _Backend()
    thread = context.JobThread(
        backend=backend,
        job_id=(job_id or str(uuid.uuid4())),
        state=state,
        extra=extra,
        fatal_internal=True,
    )
    thread.start()
    thread.join()

    if backend.end.exc is not None:
        if fatal:
            raise RuntimeError(backend.end.exc)
        else:
            get_logger().error(backend.end.exc)

    return _Result(job_id, backend.steps, backend.end)


_Step = collections.namedtuple("_Step", ("job_id", "state", "stack"))
_End = collections.namedtuple("_End", ("job_id", "retval", "exc"))
_Result = collections.namedtuple("_Result", ("job_id", "steps", "end"))


class _Backend:
    def __init__(self):
        self.steps = []
        self.end = None

        class _Stub:
            pass
        self.jobs_process = _Stub()
        self.jobs_process.save_job_state = self._save_job_state
        self.jobs_process.done_job = self._done_job

    def _save_job_state(self, job_id, state, stack):
        self.steps.append(_Step(job_id, state, stack))

    def _done_job(self, job_id, retval, exc):
        self.end = _End(job_id, retval, exc)
