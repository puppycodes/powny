from raava import task
import time
import logging

def cont_sleep(cont, secs):
    cont.switch("one sleep=%d" % (secs))
    time.sleep(secs)
    cont.switch("two sleep=%d" % (secs))

def cont_notify(cont, *args_tuple):
    cont.switch(" ".join(map(str, args_tuple)))

def foo(name, *args_tuple):
    for arg in args_tuple:
        notify(name, arg)
        sleep(2)
    notify(name, "finished!")

if __name__ == "__main__":
    logger = logging.getLogger(task.LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(name)s %(threadName)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    manager = task.TaskManager(
        lambda a, b: None,
        lambda a, b: None,
        lambda a, b: None,
    )
    task.setup_builtins({ "sleep": cont_sleep, "notify": cont_notify })

    t1 = manager.add(lambda: foo("task-1", 1, 2, 3, 4, 5))
    time.sleep(4)
    t2 = manager.add(lambda: foo("   task-2", 1, 2, 3))

