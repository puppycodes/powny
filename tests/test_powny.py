import time

from powny.core import __version__

from .fixtures.application import powny_api
from .fixtures.application import as_dict
from .fixtures.application import from_dict


# ====
def test_api_v1_rules():
    with powny_api() as (test_client, _):
        with test_client() as api:
            result = as_dict(api.get("/v1/rules"))
            assert result[0] == 200
            assert result[1] == {"head": None, "errors": None, "exposed": None}

            result = as_dict(api.post("/v1/rules", **from_dict({"head": "foobar"})))
            assert result[0] == 400
            assert result[1] == {"head": "foobar", "message": "The argument \"foobar\" is not a valid hex string"}

            result = as_dict(api.post("/v1/rules", **from_dict({"head": "0"})))
            assert result[0] == 400
            assert result[1] == {"head": "0", "message": "AssertionError: Can't find module path: rules/0"}

            result = as_dict(api.post("/v1/rules", **from_dict({"head": "0123456789abcdef"})))
            assert result[0] == 200
            assert result[1]["head"] == "0123456789abcdef"
            assert isinstance(result[1]["errors"], dict)
            assert isinstance(result[1]["exposed"]["methods"], list)
            assert isinstance(result[1]["exposed"]["handlers"], list)


def test_api_v1_system_state():
    with powny_api(with_worker=True) as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/state"))
            assert result[0] == 200
            assert result[1]["jobs"]["input"] == 0
            assert result[1]["jobs"]["all"] == 0

            assert as_dict(api.post("/v1/rules", **from_dict({"head": "0123456789abcdef"})))[0] == 200
            assert as_dict(api.post("/v1/jobs", **from_dict({})))[0]

            time.sleep(config.worker.empty_sleep + 3)

            result = as_dict(api.get("/v1/system/state"))
            assert result[0] == 200
            assert result[1]["jobs"]["input"] == 0
            assert result[1]["jobs"]["all"] == 1


def test_api_v1_system_info():
    with powny_api() as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/info"))
            assert result[0] == 200
            assert result[1]["version"] == __version__
            assert result[1]["backend"]["name"] == config.core.backend


def test_api_v1_system_config():
    with powny_api() as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/config"))
            assert result[0] == 200
            assert result[1] == config


def _test_api_v1_jobs_delete(url, kwargs):
    with powny_api() as (test_client, config):
        with test_client() as api:
            assert as_dict(api.post("/v1/rules", **from_dict({"head": "0123456789abcdef"})))[0] == 200

            result = as_dict(api.post(url, **from_dict(kwargs)))
            assert result[0] == 200
            (job_id, job_info) = tuple(result[1].items())[0]
            method_name = job_info["method"]

            result = as_dict(api.get("/v1/jobs/" + job_id))
            assert result[0] == 200
            assert result[1]["method"] == method_name
            assert result[1]["deleted"] is False

            result = as_dict(api.delete("/v1/jobs/" + job_id))
            time.sleep(config.collector.empty_sleep)

            result = as_dict(api.get("/v1/jobs/" + job_id))
            assert result[0] == 404


def test_api_v1_jobs_handler_delete():
    _test_api_v1_jobs_delete("/v1/jobs", {})


def test_api_v1_jobs_method_delete():
    _test_api_v1_jobs_delete("/v1/jobs?method=rules.test.empty_method", {})


def test_api_v1_jobs_handler_execution(smtpserver):
    _test_api_v1_jobs_execution(smtpserver, None, "rules.test.send_email_by_event_handler", 5)


def test_api_v1_jobs_method_execution(smtpserver):
    _test_api_v1_jobs_execution(smtpserver, "rules.test.send_email_by_event", "rules.test.send_email_by_event", 5)


def _test_api_v1_jobs_execution(smtpserver, method, find, repeat):
    url = "/v1/jobs"
    if method is not None:
        url += "?method=" + method
    with powny_api("""
        helpers:
            configure:
                - powny.helpers.email
            email:
                server: {server}
                port: {port}
    """.format(server=smtpserver.addr[0], port=smtpserver.addr[1]), with_worker=True) as (test_client, config):
        with test_client() as api:
            assert as_dict(api.post("/v1/rules", **from_dict({"head": "0123456789abcdef"})))[0] == 200
            result = as_dict(api.post(url, **from_dict({
                "test":   "send_email_by_event",
                "repeat": repeat,
                "sleep":  0,
            })))
            assert result[0] == 200
            for (job_id, job_info) in result[1].items():
                if job_info["method"] == find:
                    break
            else:
                job_id = None
            assert job_id is not None

            for _ in range(config.worker.empty_sleep + 300):
                result = as_dict(api.get("/v1/jobs/" + job_id))
                assert result[0] == 200
                if result[1]["finished"] is not None:
                    break
                time.sleep(1)
            assert result[0] == 200
            assert len(smtpserver.outbox) == repeat
