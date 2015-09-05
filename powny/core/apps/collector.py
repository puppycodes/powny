import time

from contextlog import get_logger

from . import (
    init,
    Application,
)


# =====
_stop = None


def run(args=None, config=None):
    if config is None:
        config = init(__name__, "Powny Garbage Collector", args)
    app = _Collector(config)
    global _stop
    _stop = app.stop
    return abs(app.run())


# =====
class _Collector(Application):
    """
        This application provides cleaning storage of data left after the execution
        of the jobs. Incomplete jobs (due to the failure) are returned to the input
        queue. The completed jobs after expiration of the lifetime are deleted.
    """

    def __init__(self, config):
        Application.__init__(self, "collector", config)
        self._processed = 0

    def process(self):
        logger = get_logger()
        with self.get_backend_object().connected() as backend:
            sleep_mode = False
            while not self._stop_event.is_set():
                sleep_mode = (not self._gc_jobs(backend))  # Separate function for a different log context
                if not sleep_mode:
                    logger.debug("No jobs in list, entering to sleep mode with interval  %f seconds...",
                                 self._app_config.empty_sleep)
                sleep_mode = True
                time.sleep(self._app_config.empty_sleep)

    def _gc_jobs(self, backend):
        processed = 0
        self._dump_collector_state(backend)
        for (job_id, done) in backend.jobs_gc.get_jobs():
            logger = get_logger(job_id=job_id)
            logger.debug("Processing: done=%s", done)
            if done:
                backend.jobs_gc.remove_job_data(job_id)
                logger.info("Removed done job")
            else:
                backend.jobs_gc.push_back_job(job_id)
                logger.info("Pushed-back unfinished job")
            processed += 1
            self._processed += 1
            self._dump_collector_state(backend)
        return bool(processed)

    def _dump_collector_state(self, backend):
        self.dump_app_state(backend, {"processed": self._processed})
