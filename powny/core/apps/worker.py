import sys
import os
import multiprocessing
import time

from contextlog import get_logger

from .. import context
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
        This application performs the jobs. Each job runs in a separate process and
        has its own connection to the backend. It automatically saves the state of
        the job. Worker only ensures that the process must be stopped upon request.
    """

    def __init__(self, config):
        Application.__init__(self, "worker", config)
        self._manager = _JobsManager(self._config.core.rules_dir)
        self._not_started = 0

    def process(self):
        logger = get_logger()
        sleep_mode = False
        with self.get_backend_object().connected() as backend:
            while not self._stop_event.is_set():
                gen_jobs = backend.jobs_process.get_ready_jobs()
                while not self._stop_event.is_set():
                    self._manager.manage(backend)
                    self._write_worker_state(backend)

                    if self._manager.get_current() >= self._app_config.max_jobs:
                        logger.debug("Have reached the maximum concurrent jobs (%d), sleeping %f seconds...",
                                     self._app_config.max_jobs, self._app_config.max_jobs_sleep)
                        time.sleep(self._app_config.max_jobs_sleep)

                    else:
                        try:
                            job = next(gen_jobs)
                        except StopIteration:
                            if not sleep_mode:
                                logger.debug("No jobs in queue, entering to sleep mode with interval %f seconds...",
                                             self._app_config.empty_sleep)
                            sleep_mode = True
                            time.sleep(self._app_config.empty_sleep)
                            break
                        else:
                            sleep_mode = False
                            if not self._manager.run_job(job, self.get_backend_object()):
                                backend.jobs_process.release_job(job.job_id)
                                self._not_started += 1

    def _write_worker_state(self, backend):
        self.set_app_state(backend, {
            "active":      self._manager.get_current(),
            "processed":   self._manager.get_finished(),
            "not_started": self._not_started,
        })


class _JobsManager:
    def __init__(self, rules_dir):
        self._rules_dir = rules_dir
        self._procs = {}
        self._finished = 0

    def get_finished(self):
        return self._finished

    def get_current(self):
        return len(self._procs)

    def run_job(self, job, backend):
        logger = get_logger(job_id=job.job_id)
        logger.info("Starting the job process")
        associated = multiprocessing.Event()
        proc = multiprocessing.Process(target=_exec_job, args=(job, self._rules_dir, backend, associated))
        self._procs[job.job_id] = proc
        proc.start()
        if not associated.wait(1):
            logger.error("Cannot associate job after one second")
            self._kill(proc)
            return False
        return True

    def manage(self, backend):
        for (job_id, proc) in self._procs.copy().items():
            logger = get_logger(job_id=job_id)
            if not proc.is_alive():
                logger.info("Finished job process %d with retcode %d", proc.pid, proc.exitcode)
                self._finish(job_id)
            elif backend.jobs_process.is_deleted_job(job_id):
                self._kill(proc)
                self._finish(job_id)

    def _finish(self, job_id):
        self._procs.pop(job_id)
        self._finished += 1

    def _kill(self, proc):
        logger = get_logger()
        logger.info("Killing job process %s...", proc)
        try:
            proc.terminate()
            proc.join()
        except Exception:
            logger.exception("Can't kill process %s; ignored", proc)
            return
        logger.info("Killed job process %d with retcode %d", proc.pid, proc.exitcode)


def _exec_job(job, rules_dir, backend, associated):
    logger = get_logger(job_id=job.job_id)
    rules_path = tools.make_rules_path(rules_dir, job.version)
    with backend.connected():
        logger.debug("Associating job with PID %d", os.getpid())
        backend.jobs_process.associate_job(job.job_id)
        associated.set()

        sys.path.insert(0, rules_path)
        thread = context.JobThread(
            backend=backend,
            job_id=job.job_id,
            state=job.state,
            extra={"number": job.number, "version": job.version},
        )
        thread.start()
        thread.join()
