import contextlib
import threading
import uuid
import json
from powny.core.apps import (
    api,
    worker,
    collector,
)
from powny.testing.application import configured


# =====
@contextlib.contextmanager
def powny_api(text=None):
    with configured(text) as config:
        chroot = "/" + str(uuid.uuid4())
        config["backend"]["chroot"] = chroot
        try:
            api_app = api.make_app(config)
            api_app.debug = True
            api_app.testing = True
            yield (api_app.test_client, config)
        finally:
            # Cleanup ZooKeeper
            if config.core.backend == "zookeeper":
                from powny.backends.zookeeper import zoo
                zclient_kwargs = dict(config.backend)
                zclient_kwargs["chroot"] = None
                with zoo.Client(**zclient_kwargs).connected() as client:
                    with client.make_write_request("remove_chroot()") as request:
                        request.delete(chroot, recursive=True)
            else:
                raise NotImplementedError


def as_dict(response):
    return (response.status_code, json.loads(response.data.decode()))


def from_dict(attrs):
    return {
        "headers": {"Content-Type": "application/json"},
        "data": json.dumps(attrs).encode(),
    }


@contextlib.contextmanager
def running_worker(config):
    try:
        thread = threading.Thread(target=worker.run, kwargs={"config": config})
        thread.daemon = True
        thread.start()
        yield
    finally:
        worker._stop()  # pylint: disable=protected-access
        thread.join()


@contextlib.contextmanager
def running_collector(config):
    try:
        thread = threading.Thread(target=collector.run, kwargs={"config": config})
        thread.daemon = True
        thread.start()
        yield
    finally:
        collector._stop()  # pylint: disable=protected-access
        thread.join()
