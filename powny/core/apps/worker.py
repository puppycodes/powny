import sys
import os
import signal
import multiprocessing
import threading
import setproctitle
import logging
import errno
import time

from contextlog import get_logger

from .. import context

from . import (
    init,
    Application,
)


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
        self._jobs_limit = None
        self._procs = {}
        self._finished = 0
        self._not_started = 0

    def process(self):
        logger = get_logger()

        with self.get_backend_object().connected() as backend:
            while not self._stop_event.is_set():
                self._set_jobs_limit(backend)
                self._manage_processes(backend)
                self._dump_worker_state(backend)

                if len(self._procs) >= self._jobs_limit:
                    logger.debug("Have reached the maximum concurrent jobs %d, sleeping %f seconds...",
                                 self._jobs_limit, self._app_config.max_jobs_sleep)
                    time.sleep(self._app_config.max_jobs_sleep)

                elif backend.jobs_process.has_ready_jobs():
                    if not self._try_start_job():
                        logger.debug("No jobs to start, sleeping for %f seconds...", self._app_config.empty_sleep)
                        time.sleep(self._app_config.empty_sleep)

    def _manage_processes(self, backend):
        for (job_id, proc) in self._procs.copy().items():
            logger = get_logger(job_id=job_id)

            alive = proc.is_alive()
            deleted = backend.jobs_process.is_deleted_job(job_id)

            if not alive or deleted:
                if deleted:
                    logger.info("Terminating job process %d...", proc.pid)
                    try:
                        proc.terminate()
                        logger.info("Terminated")
                    except Exception:
                        logger.exception("Can't terminate process %d; ignored", proc.pid)
                proc.join()
                self._procs.pop(job_id)
                self._finished += 1
                logger.info("Finished job process %d with retcode %d", proc.pid, proc.exitcode)

    def _set_jobs_limit(self, backend):
        if self._app_config.max_jobs is None:
            all_jobs = backend.jobs_control.get_jobs_count()
            workers = max(len(backend.system_apps_state.get_full_state().get("worker", {})), 1)
            jobs_limit = int(all_jobs / workers + 1)
        else:
            jobs_limit = self._app_config.max_jobs

        if self._jobs_limit != jobs_limit:
            get_logger().info("Set new jobs limit: %d", jobs_limit)
            self._jobs_limit = jobs_limit

    def _dump_worker_state(self, backend):
        self.dump_app_state(backend, {
            "active": len(self._procs),
            "processed": self._finished,
            "not_started": self._not_started,
            "jobs_limit": self._jobs_limit,
        })

    def _try_start_job(self):
        logger = get_logger()
        logger.debug("Starting candidate process")

        nothing = multiprocessing.Event()
        launched = multiprocessing.Event()
        return_info = multiprocessing.Manager().dict()  # pylint: disable=no-member

        proc = multiprocessing.Process(
            target=_find_job_and_run,
            kwargs={
                "backend": self.get_backend_object(),
                "scripts_dir": self._config.core.scripts_dir,
                "return_info": return_info,
                "nothing": nothing,
                "launched": launched,
            },
        )
        proc.start()
        launched.wait(self._app_config.wait_slowpokes)

        if launched.is_set():  # Задача нашлась и запущена
            self._procs[return_info["job_id"]] = proc
            return True
        elif nothing.is_set():  # Задач нет, надо поспать
            proc.join()
            return False
        else:  # Слоупок
            logger.error("Detected slowpoke process %d", proc.pid)
            killed = _send_signal(proc, signal.SIGKILL)
            proc.join()
            if killed:
                logger.info("Killed slowpoke job process %d with retcode %d", proc.pid, proc.exitcode)
            else:
                logger.info("Found dead slowpoke job process %d with retcode %d", proc.pid, proc.exitcode)
            self._not_started += 1


def _send_signal(proc, signum):
    try:
        os.kill(proc.pid, signum)
        return True
    except OSError as err:
        if err.errno == errno.ESRCH:
            return False
        raise


def _find_job_and_run(backend, scripts_dir, nothing, launched, return_info):
    sys.dont_write_bytecode = True
    _unlock_logging()
    try:
        with backend.connected():
            job = backend.jobs_process.get_job()
            if job is None:
                get_logger().debug("Nothing to run; exit")
                nothing.set()
                return

            scripts_path = os.path.join(scripts_dir, job.head)
            sys.path.insert(0, scripts_path)
            logger = get_logger(job_id=job.job_id)
            logger.info("Starting the job")
            _rename_process(job)

            thread = context.JobThread(
                backend=backend,
                job_id=job.job_id,
                state=job.state,
                extra={"head": job.head},
                fatal_internal=(not job.respawn),
            )
            thread.start()
            return_info["job_id"] = job.job_id
            launched.set()
            thread.join()
    except Exception:
        logger.exception("Unhandled exception in subprocess")
        raise


def _rename_process(job):
    setproctitle.setproctitle("[worker: {}] {}".format(  # pylint: disable=no-member
        job.job_id,
        setproctitle.getproctitle(),  # pylint: disable=no-member
    ))


def _unlock_logging():
    # XXX: ULTIMATE EPIC-SIZED CRUTCH!!!111
    # http://bugs.python.org/issue6721
    if logging._lock:  # pylint: disable=protected-access
        logging._lock = threading.RLock()  # pylint: disable=protected-access
    for wr in logging._handlerList:  # pylint: disable=protected-access
        handler = wr()
        if handler and handler.lock:
            handler.lock = threading.RLock()
