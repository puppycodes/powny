import contextlib
import textwrap
import threading
import uuid
import json

from powny.core import apps
from powny.core.apps import api
from powny.core.apps import worker
from powny.core.apps import collector

from .tmp import write_file


# =====
@contextlib.contextmanager
def configured(text=None):
    if text is not None:
        with write_file(textwrap.dedent(text)) as file_path:
            config = apps.init("test", "Test case", ["-c", file_path])
    else:
        config = apps.init("test", "Test case", [])
    try:
        yield config
    finally:
        apps._config = None  # pylint: disable=protected-access


@contextlib.contextmanager
def powny_api(text=None, with_worker=False):
    with configured(text) as config:
        chroot = "/" + str(uuid.uuid4())
        config["backend"]["chroot"] = chroot
        try:
            if with_worker:
                worker_thread = threading.Thread(target=worker.run, kwargs={"config": config})
                worker_thread.daemon = True
                worker_thread.start()

            collector_thread = threading.Thread(target=collector.run, kwargs={"config": config})
            collector_thread.daemon = True
            collector_thread.start()

            (_, api_pool, api_app) = api.make_app(  # pylint: disable=unpacking-non-sequence
                only_return=False,
                config=config,
            )
            with api_pool:
                api_app.debug = True
                api_app.testing = True
                yield (api_app.test_client, config)
        finally:
            if with_worker:
                worker._stop()  # pylint: disable=protected-access
                worker_thread.join()

            collector._stop()  # pylint: disable=protected-access
            collector_thread.join()

# TODO FIXME XXX: WHAT THE FUCK?!
# [zk: localhost:2181(CONNECTED) 40] ls /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
# []
# [zk: localhost:2181(CONNECTED) 41] delete /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
# Node not empty: /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
#
#            if config.core.backend == "zookeeper":
#                from powny.backends.zookeeper import zoo
#                zclient_kwargs = dict(config.backend)
#                zclient_kwargs["chroot"] = None
#                with zoo.Client(**zclient_kwargs) as client:
#                    with client.get_write_request("remove_chroot()") as request:
#                        request.delete(chroot, recursive=True)
#            else:
#                raise NotImplementedError


def as_dict(response):
    return (response.status_code, json.loads(response.data.decode()))


def from_dict(attrs):
    return {
        "headers": {"Content-Type": "application/json"},
        "data":    json.dumps(attrs).encode(),
    }
