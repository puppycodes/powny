import sys
import os
import multiprocessing
import pprint
import logging
import time
import abc

from contextlog import get_logger

from .. import context
from .. import backends
from .. import tools

from . import init
from . import Application


# =====
_stop = None

def run(args=None, config=None):
    if config is None:
        config = init(__name__, "Powny Worker", args)
    app = _Worker(config)
    global _stop
    _stop = app.stop
    return abs(app.run())


# =====
class _Worker(Application):
    """
        -=-=-= PROCESSES SCHEME =-=-=-

                                        +================+
                            appstate    |                |
                        --------------> | State (writer) |
                        |               |                |
                        |               +================+
                        |
                        |
        +=================+   request   +=============================+
        |                 | ----------> |                             |
        | Worker (master) |             | Generator (polls the queue) |
        |                 | <---------- |                             |
        +=================+     job     +=============================+
          |          ^  |
          |          |  |
          | spawn    |  |   jobs ids    +=================================+
          | or       |  `-------------> |                                 |
          | kill     |                  | Killer (checks DELETE requests) |
          |          `----------------- |                                 |
         ... (many)       ids to kill   +=================================+
          |
          V
        +===========================+
        |                           |
        | Job (real worker in fact) |
        |                           |
        +===========================+
    """

    def __init__(self, config):
        Application.__init__(self, "worker", config)
        self._state_proc = None
        self._generator_proc = None
        self._killer_proc = None
        self._jobs_children = {}
        self._processed = 0

    def process(self):
        logger = get_logger()

        logger.debug("Starting the state process")
        self._state_proc = _StateProcess(self._config.core.backend, self._config.backend)
        self._state_proc.start()

        logger.debug("Starting the generator process")
        self._generator_proc = _GeneratorProcess(self._config.core.backend, self._config.backend)
        self._generator_proc.start()

        logger.debug("Starting the killer process")
        self._killer_proc = _KillerProcess(self._config.core.backend, self._config.backend)
        self._killer_proc.start()

        logger.info("Ready to work")
        sleep_mode = False
        while not self._stop_event.is_set():
            for proc in (self._state_proc, self._generator_proc, self._killer_proc):
                if not proc.is_alive():
                    raise RuntimeError("Crashed process {}: pid={}; retcode={}".format(
                                       proc, proc.pid, proc.exitcode))
            self._manage_jobs()

            if len(self._jobs_children) >= self._app_config.max_jobs:
                logger.debug("Have reached the maximum concurrent jobs (%d), sleeping %f seconds...",
                             self._app_config.max_jobs, self._app_config.max_jobs_sleep)
                time.sleep(self._app_config.max_jobs_sleep)
            else:
                job = self._generator_proc.make_request()
                if job is None:
                    if not sleep_mode:
                        logger.debug("No jobs in queue, entering to sleep mode with interval %f seconds...",
                                     self._app_config.empty_sleep)
                    sleep_mode = True
                    time.sleep(self._app_config.empty_sleep)
                else:
                    sleep_mode = False
                    logger.info("Starting the job process", job_id=job.job_id)
                    job_proc = _JobProcess(
                        job=job,
                        rules_dir=self._config.core.rules_dir,
                        backend_name=self._config.core.backend,
                        backend_kwargs=self._config.backend,
                    )
                    self._jobs_children[job.job_id] = job_proc
                    job_proc.start()

    def respawn(self):
        for proc in (self._state_proc, self._generator_proc, self._killer_proc):
            self._kill(proc)

    def cleanup(self):
        for proc in (self._state_proc, self._generator_proc, self._killer_proc) + tuple(self._jobs_children.values()):
            self._kill(proc)

    def _kill(self, proc):
        logger = get_logger()
        logger.info("Killing %s...", proc)
        try:
            proc.terminate()
            proc.join()
        except Exception:
            logger.exception("Can't kill process %s; ignored", proc)

    def _manage_jobs(self):
        for (job_id, job_proc) in tuple(self._jobs_children.items()):
            if not job_proc.is_alive():
                get_logger().info("Finished job process %d with retcode %d",
                                  job_proc.pid, job_proc.exitcode, job_id=job_id)
                self._jobs_children.pop(job_id)
                self._processed += 1

        for job_id in self._killer_proc.make_request(tuple(self._jobs_children)):
            job_proc = self._jobs_children.get(job_id)
            if job_proc is not None:
                self._kill(job_proc)
                job_proc.join()
                self._jobs_children.pop(job_id)
                self._processed += 1
                get_logger().info("Killed (on DELETE) job process %d with retcode %d",
                                  job_proc.pid, job_proc.exitcode, job_id=job_id)

        self._state_proc.make_request(self.make_write_app_state({
            "active":    len(self._jobs_children),
            "processed": self._processed,
        }))


class _DialogProcess(multiprocessing.Process, metaclass=abc.ABCMeta):
    def __init__(self, backend_name, backend_kwargs):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        (self._conn_ext, self._conn_int) = multiprocessing.Pipe()
        self._backend = backends.get_backend(backend_name)(**backend_kwargs)

    def make_request(self, request=None):
        self._conn_ext.send(request)
        return self._conn_ext.recv()

    def run(self):
        with self._backend:
            while True:
                self.loop()

    @abc.abstractmethod
    def loop(self):  # Makes pylint happy
        raise NotImplementedError


class _KillerProcess(_DialogProcess):
    def loop(self):
        self._conn_int.send(list(
            job_id for job_id in self._conn_int.recv()
            if self._backend.jobs.process.is_deleted_job(job_id)
        ))


class _GeneratorProcess(_DialogProcess):
    def loop(self):
        gen_jobs = self._backend.jobs.process.get_ready_jobs()
        while True:
            self._conn_int.recv()
            try:
                self._conn_int.send(next(gen_jobs))
            except StopIteration:
                self._conn_int.send(None)
                break


class _StateProcess(_DialogProcess):
    def loop(self):
        self._backend.system.apps_state.set_state(*self._conn_int.recv())
        self._conn_int.send(None)


class _JobProcess(multiprocessing.Process):
    def __init__(self, job, rules_dir, backend_name, backend_kwargs):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self._job = job
        self._rules_path = tools.make_rules_path(rules_dir, self._job.version)
        self._backend = backends.get_backend(backend_name)(**backend_kwargs)

    def run(self):
        sys.path.insert(0, self._rules_path)
        logger = get_logger(job_id=self._job.job_id)
        with self._backend:
            logger.debug("Associating job with PID %d", os.getpid())
            self._backend.jobs.process.associate_job(self._job.job_id)

            job_thread = context.JobThread(
                save_context=self._save_context,
                job_id=self._job.job_id,
                func=(self._job.func if self._job.state is None else None),
                kwargs=self._job.kwargs,
                state=self._job.state,
                extra={
                    "number":  self._job.number,
                    "version": self._job.version,
                },
            )
            job_thread.start()
            job_thread.join()

    def _save_context(self, step):
        if not step.done:
            stack = (step.stack_or_retval and [
                item for item in step.stack_or_retval
                if item[0].startswith(self._rules_path)
            ])

            logger = get_logger(job_id=self._job.job_id)
            if logger.getEffectiveLevel() <= logging.DEBUG:
                logger.debug("Interesting stack snapshot:\n%s", pprint.pformat(stack))

            self._backend.jobs.process.save_job_state(
                job_id=step.job_id,
                state=step.state,
                stack=stack,
            )
        else:
            self._backend.jobs.process.done_job(
                job_id=step.job_id,
                retval=step.stack_or_retval,
                exc=step.exc,
            )
