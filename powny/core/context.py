import traceback
import inspect
import pickle
import copy
import threading

from contextlog import get_logger


# =====
class SuicideError(Exception):
    pass


def suicide(msg):
    raise SuicideError(msg)


def in_context():
    thread = threading.current_thread()
    return isinstance(thread, JobThread)


def get_context():
    assert in_context(), "Called not from a job context!"
    return threading.current_thread()


def get_job_id():
    return get_context().get_job_id()  # pylint: disable=maybe-no-member


def get_extra():
    return get_context().get_extra()  # pylint: disable=maybe-no-member


def get_cas_storage():
    return get_context().get_cas_storage()  # pylint: disable=maybe-no-member


def save_job_state():
    return get_context().save()  # pylint: disable=maybe-no-member


# =====
def dump_call(method, kwargs):
    """ Собирает из метода и его аргументов континулет и пиклит его """

    get_logger().debug("Creating a new continulet...")
    import _continuation
    return pickle.dumps(_continuation.continulet(lambda _: method(**kwargs)))


def restore_call(state):
    """ Распикливает состояние (континулет) для запуска """

    get_logger().debug("Restoring the continulet state...")
    import _continuation
    cont = pickle.loads(state)
    assert isinstance(cont, _continuation.continulet), "The unpickled state is a garbage!"
    return cont


class JobThread(threading.Thread):
    """
        JobThread() предназначен для запуска ранее запикленной в континулет функции (с помощью dump_call()).
        Внутри потока континулет распикливается и исполняется, сохраняя свое состояние в переданный бекенд
        функциями backend.jobs_process.save_job_state() и backend.jobs_process.done_job().
        Поток нужен не только для исполнения континулета, но и для того, чтобы изнутри континулета можно было
        получить метаданные текущей задачи, используя threading.current_thread().
    """

    def __init__(self, backend, job_id, state, extra, fatal_internal,  # pylint: disable=unused-argument
                 __unpickle=False):

        threading.Thread.__init__(self, name="JobThread::" + job_id)
        self._backend = backend
        self._job_id = job_id
        self._state = state
        self._extra = extra
        self._fatal_internal = fatal_internal
        self._cont = None
        self._log_context = get_logger().get_context()  # Proxy context into the continulet

    def __getstate__(self):
        # Шаг 1. Запикливаемся, как строка с айдишником задачи. Он нужен только для того, чтобы
        #        проверить, что потом мы распиклились в новом контексте, но с тем же айдишником.
        #        При распикливании новый объект не создается, а возвращается ссылка на текущий
        #        контекст, чтобы одну и ту же задачу не представляло два разных объекта (хоть и
        #        с одинаковым стейтом).
        return self._job_id

    def __getnewargs__(self):
        # Шаг 2. Распикливаемся, передавая в __new__ аргумент о том, что мы именно распикливаемся,
        #        а не создаем новый контекст.
        #        https://docs.python.org/3.2/library/pickle.html#pickle.object.__getnewargs__
        return ((None,) * 5) + (True,)  # Unpickle as current context

    def __new__(cls, backend, job_id, state, extra, fatal_internal, __unpickle=False):
        if __unpickle:
            # Шаг 3. При распикливании, вместо создания нового объекта, возвращаем ссылку на текущий
            #        контекст, предполагая, что он и является контекстом той задачи, в которой
            #        произошло распикливание.
            context = get_context()
            return context  # Return the current context instead of the new object
        else:
            return super(JobThread, cls).__new__(cls, backend, job_id, state, extra, fatal_internal)

    def __setstate__(self, job_id):
        # Шаг 4. После распикливания, проверяем, что мы распиклились в правильном контексте. Айдишник
        #        задачи текущего контекста должен совпадать с айдишником объекта и с тем айдишником,
        #        контекст которого хотели распиклить.
        assert get_context().get_job_id() == self._job_id == job_id  # pylint: disable=maybe-no-member

    ###

    def get_job_id(self):
        return self._job_id

    def get_extra(self):
        return copy.deepcopy(self._extra)

    def get_cas_storage(self):
        return self._backend.cas_storage

    def save(self):
        stack = traceback.extract_stack(inspect.currentframe())
        self._cont.switch(stack)

    ###

    def run(self):
        logger = get_logger(**self._log_context)

        logger.debug("Initializing context...")
        try:
            self._cont = restore_call(self._state)
        except Exception:
            logger.exception("Context initialization has failed")
            self._backend.jobs_process.done_job(
                job_id=self._job_id,
                retval=None,
                exc=traceback.format_exc(),
            )
            raise

        logger.debug("Activation...")
        while self._cont.is_pending():
            try:
                logger.debug("Entering continulet...")
                stack_or_retval = self._cont.switch()
                logger.debug("Exited from continulet")
                if self._cont.is_pending():  # In progress
                    self._backend.jobs_process.save_job_state(
                        job_id=self._job_id,
                        state=pickle.dumps(self._cont),
                        stack=stack_or_retval,
                    )
                else:  # Done
                    self._backend.jobs_process.done_job(
                        job_id=self._job_id,
                        retval=stack_or_retval,
                        exc=None,
                    )
            except Exception as err:
                if isinstance(err, SuicideError):
                    logger.info("Suicide; fatal_internal=%s", self._fatal_internal)
                else:
                    logger.exception("Unhandled step error; fatal_internal=%s", self._fatal_internal)
                # self._cont.switch() switches the stack, so we will see a valid exception, up to this place
                # in the script. sys.exc_info() return a raw exception data. Some of them can't be pickled, for
                # example, traceback-object. For those who use the API, easier to read the text messages.
                # traceback.format_exc() simply converts data from sys.exc_info() into a string.
                if self._fatal_internal:
                    self._backend.jobs_process.done_job(
                        job_id=self._job_id,
                        retval=None,
                        exc=traceback.format_exc(),
                    )
                logger.debug("Context failed")
                return
        logger.debug("Context finished")
