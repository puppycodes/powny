import traceback
import inspect
import pickle
import copy
import threading
import collections

from contextlog import get_logger


# =====
_fake_context = None  # For tests

def get_context():
    if _fake_context is not None:
        return _fake_context
    thread = threading.current_thread()
    assert isinstance(thread, JobThread), "Called not from a job context!"
    job_context = thread.get_job_context()  # pylint: disable=E1103
    del thread
    return _JobContextProxy(job_context)


Step = collections.namedtuple("Step", (
    "job_id",
    "state",
    "stack_or_retval",
    "exc",
    "done",
))


class JobThread(threading.Thread):
    def __init__(self, save_context, *args, **kwargs):
        self._save_context = save_context  # save_context(job_id, state, stack_or_retval, exc)
        self._job_context = _JobContext(*args, **kwargs)
        self._job_id = self._job_context.get_job_id()
        threading.Thread.__init__(self, name="JobThread::" + self._job_id)

    def get_job_context(self):
        return self._job_context

    def run(self):
        logger = get_logger(job_id=self._job_id)

        try:
            self._job_context.init()
        except Exception:
            logger.exception("Context initialization has failed")
            self._save_context(Step(
                job_id=self._job_id,
                state=None,
                stack_or_retval=None,
                exc=traceback.format_exc(),
                done=True,
            ))
            return

        for step in self._job_context.step_by_step():
            self._save_context(step)

        logger.info("Finished")


# =====
class _JobContextProxy:
    def __init__(self, job_context):
        self.get_job_id = job_context.get_job_id
        self.get_extra = job_context.get_extra
        self.save = job_context.save


class _JobContext:
    def __init__(self, job_id, func, kwargs, state, extra):
        assert bool(func) ^ bool(state), "Required func OR state"
        self._job_id = job_id
        self._func = func
        self._kwargs = (kwargs or {})
        self._state = state
        self._extra = extra
        self._cont = None

    def get_job_id(self):
        return self._job_id

    def get_extra(self):
        return copy.deepcopy(self._extra)

    def save(self):
        stack = traceback.extract_stack(inspect.currentframe())
        self._cont.switch(stack)

    def init(self):
        import _continuation
        logger = get_logger(job_id=self._job_id)
        if self._func is not None:
            logger.debug("Creating a new continulet...")
            method = pickle.loads(self._func)
            cont = _continuation.continulet(lambda _: method(**self._kwargs))
        elif self._state is not None:
            logger.debug("Restoring the old state...")
            cont = pickle.loads(self._state)
            assert isinstance(cont, _continuation.continulet), "The unpickled state is a garbage!"
        logger.debug("Continulet is ready to run")
        self._cont = cont

    def step_by_step(self):
        logger = get_logger(job_id=self._job_id)
        logger.debug("Activation...")
        while self._cont.is_pending():
            try:
                stack_or_retval = self._cont.switch()
                yield Step(
                    job_id=self._job_id,
                    state=pickle.dumps(self._cont),
                    stack_or_retval=stack_or_retval,
                    exc=None,
                    done=(not self._cont.is_pending())
                )
            except Exception:
                logger.exception("Unhandled step error")
                # self._cont.switch() switches the stack, so we will see a valid exception, up to this place
                # in the rule. sys.exc_info() return a raw exception data. Some of them can't be pickled, for
                # example, traceback-object. For those who use the API, easier to read the text messages.
                # traceback.format_exc() simply converts data from sys.exc_info() into a string.
                yield Step(
                    job_id=self._job_id,
                    state=None,
                    stack_or_retval=None,
                    exc=traceback.format_exc(),
                    done=True,
                )
                break
        logger.debug("Job finished")
