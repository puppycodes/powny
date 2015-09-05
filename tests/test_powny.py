import pprint
import time

from powny.core import __version__

from .fixtures.application import (
    powny_api,
    as_dict,
    from_dict,
    running_worker,
    running_collector,
)


# ====
def test_api_v1_scripts():
    with powny_api() as (test_client, _):
        with test_client() as api:
            result = as_dict(api.get("/v1/scripts/exposed"))
            assert result == (200, {
                "status": "ok",
                "message": "The scripts of current HEAD",
                "result": {"head": None, "errors": None, "exposed": None},
            })

            # ---
            result = as_dict(api.post("/v1/scripts/head", **from_dict({"head": "foobar"})))
            assert result == (400, {
                "status": "error",
                "message": "The HEAD must be a hex string",
                "result": {"head": "foobar"},
            })
            result = as_dict(api.get("/v1/scripts/exposed"))
            assert result == (200, {
                "status": "ok",
                "message": "The scripts of current HEAD",
                "result": {"head": None, "errors": None, "exposed": None},
            })

            # ---
            result = as_dict(api.post("/v1/scripts/head", **from_dict({"head": "0"})))
            assert result == (200, {
                "status": "ok",
                "message": "The HEAD has been updated",
                "result": {"head": "0"},
            })
            result = as_dict(api.get("/v1/scripts/exposed"))
            assert result == (503, {
                "status": "error",
                "message": "AssertionError: Can't find module path: scripts/0",
                "result": {"head": "0", "errors": None, "exposed": None},
            })

            # ---
            result = as_dict(api.post("/v1/scripts/head", **from_dict({"head": "0123456789abcdef"})))
            assert result == (200, {
                "status": "ok",
                "message": "The HEAD has been updated",
                "result": {"head": "0123456789abcdef"},
            })

            result = as_dict(api.get("/v1/scripts/exposed"))
            assert result[0] == 200
            assert result[1]["status"] == "ok"
            assert result[1]["message"] == "The scripts of current HEAD"
            assert result[1]["result"]["head"] == "0123456789abcdef"
            assert isinstance(result[1]["result"]["errors"], dict)
            assert isinstance(result[1]["result"]["exposed"], list)


def test_api_v1_system_state():
    with powny_api() as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/state"))
            assert result[0] == 200
            assert result[1]["status"] == "ok"
            assert result[1]["message"] == "The system statistics"
            assert result[1]["result"]["jobs"]["input"] == 0
            assert result[1]["result"]["jobs"]["all"] == 0

            _init_head(api)

            with running_worker(config):
                assert as_dict(api.post("/v1/jobs?method=scripts.test.empty_method", **from_dict({})))[0]
                time.sleep(config.worker.empty_sleep + 3)
                result = as_dict(api.get("/v1/system/state"))
                assert result[0] == 200
                assert result[1]["result"]["jobs"]["input"] == 0
                assert result[1]["result"]["jobs"]["all"] == 1


def test_api_v1_system_info():
    with powny_api() as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/info"))
            assert result[0] == 200
            assert result[1]["status"] == "ok"
            assert result[1]["message"] == "The system information"
            assert result[1]["result"]["version"] == __version__
            assert result[1]["result"]["backend"]["name"] == config.core.backend


def test_api_v1_system_config():
    with powny_api() as (test_client, config):
        with test_client() as api:
            result = as_dict(api.get("/v1/system/config"))
            assert result == (200, {
                "status": "ok",
                "message": "The system configuration",
                "result": config,
            })


def test_api_v1_jobs_delete():
    with powny_api() as (test_client, config):
        with running_collector(config):
            with test_client() as api:
                _init_head(api)

                result = as_dict(api.post("/v1/jobs?method=scripts.test.empty_method"))
                assert result[0] == 200
                (job_id, job_info) = tuple(result[1]["result"].items())[0]
                method_name = job_info["method"]

                result = as_dict(api.get("/v1/jobs/" + job_id))
                assert result[0] == 200
                assert result[1]["result"]["method"] == method_name
                assert result[1]["result"]["deleted"] is None

                assert as_dict(api.delete("/v1/jobs/" + job_id))[0] == 200
                assert as_dict(api.get("/v1/jobs/" + job_id))[0] == 404


def test_api_v1_jobs_do_urlopen(httpserver):
    _test_api_v1_jobs_do_urlopen(httpserver)


def test_api_v1_jobs_do_urlopen_custom_id(httpserver):
    _test_api_v1_jobs_do_urlopen(httpserver, "urlopen_job")


def _test_api_v1_jobs_do_urlopen(httpserver, job_id=None):
    httpserver.serve_content(content="test", code=200, headers=None)
    with powny_api() as (test_client, config):
        with test_client() as api:
            _init_head(api)

            handle = "/v1/jobs?method=scripts.test.do_urlopen"
            if job_id is not None:
                handle += "&job_id={}".format(job_id)
            result = as_dict(api.post(handle, **from_dict({"url": httpserver.url})))
            assert result[0] == 200
            job_id = tuple(result[1]["result"])[0]

            with running_worker(config):
                result = _wait_unlock_job(api, job_id, config.worker.empty_sleep + 300)
                assert result["locked"] is None, pprint.pformat(result)
                assert result["finished"] is not None, pprint.pformat(result)
                assert result["exc"] is None, pprint.pformat(result)


def test_api_v1_jobs_failed_once(httpserver):
    httpserver.serve_content(content="test", code=200, headers=None)
    with powny_api() as (test_client, config):
        with test_client() as api:
            _init_head(api)

            result = as_dict(api.post("/v1/jobs?method=scripts.test.failed_once&respawn=true",
                                      **from_dict({"url": httpserver.url})))
            assert result[0] == 200
            job_id = tuple(result[1]["result"])[0]

            with running_worker(config):
                time.sleep(config.worker.empty_sleep + 3)
                result = _wait_unlock_job(api, job_id, config.worker.empty_sleep + 300)
                # Unfinished job
                assert result["locked"] is None, pprint.pformat(result)
                assert len(result["stack"] or ()) != 0, pprint.pformat(result)
                assert result["finished"] is None, pprint.pformat(result)

            with running_collector(config):
                for _ in range(int(config.collector.empty_sleep + 300)):
                    result = as_dict(api.get("/v1/jobs/" + job_id))
                    assert result[0] == 200
                    if result[1]["result"]["taken"] is None:
                        break

            with running_worker(config):
                time.sleep(config.worker.empty_sleep + 3)
                result = _wait_unlock_job(api, job_id, config.worker.empty_sleep + 300)
                # Finished job
                assert result["locked"] is None, pprint.pformat(result)
                assert result["stack"] is None, pprint.pformat(result)
                assert result["finished"] is not None, pprint.pformat(result)
                assert result["retval"] == "OK", pprint.pformat(result)


def _init_head(api):
    assert as_dict(api.post("/v1/scripts/head", **from_dict({"head": "0123456789abcdef"})))[0] == 200


def _wait_unlock_job(api, job_id, wait):
    for _ in range(int(wait)):
        result = as_dict(api.get("/v1/jobs/" + job_id))
        assert result[0] == 200
        result = result[1]["result"]
        if result["locked"] is None and result["taken"] is not None:
            return result
    raise RuntimeError("I can't wait more!")
