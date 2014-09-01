# pylint: disable=R0904
# pylint: disable=W0212
# pylint: disable=W0621


import threading
import time

import pytest

from powny.core import backends
from powny.backends.zookeeper import scheme

from .fixtures.zookeeper import zclient  # pylint: disable=W0611


# =====
class TestSchemeInit:
    def test_init(self, zclient):
        assert scheme.init(zclient)
        assert not scheme.init(zclient)


class TestJobsScheme:
    func_version = "0123456789abcdef"
    func_name = "method"
    func = b"pickled_function"
    func_kwargs = {"a": 1, "b": 2}

    def test_get_input_size(self, zclient):
        assert scheme.init(zclient)
        control_scheme = scheme.JobsControlScheme(zclient)
        assert control_scheme.get_input_size() == 0
        for count in range(5):
            control_scheme.add_job(self.func_version, self.func_name, self.func, self.func_kwargs)
            assert control_scheme.get_input_size() == count + 1

    def test_delete_wait(self, zclient):
        assert scheme.init(zclient)
        control_scheme = scheme.JobsControlScheme(zclient)
        process_scheme = scheme.JobsProcessScheme(zclient)
        gc_scheme = scheme.JobsGcScheme(zclient)

        job_id = control_scheme.add_job(self.func_version, self.func_name, self.func, self.func_kwargs)
        assert len(control_scheme.get_job_info(job_id)) > 0
        assert not process_scheme.is_deleted_job(job_id)

        ready_job = next(process_scheme.get_ready_jobs())
        assert job_id == ready_job.job_id
        process_scheme.associate_job(job_id)

        def remove_job():
            time.sleep(3)
            gc_scheme.remove_job_data(job_id)

        remover = threading.Thread(target=remove_job)
        remover.daemon = True
        remover.start()

        before = time.time()
        with pytest.raises(backends.DeleteTimeoutError):
            control_scheme.delete_job(job_id, timeout=1)
        control_scheme.delete_job(job_id)
        assert time.time() - before >= 3
        assert control_scheme.get_job_info(job_id) is None

    def test_remove_fresh_job(self, zclient):
        assert scheme.init(zclient)
        control_scheme = scheme.JobsControlScheme(zclient)
        process_scheme = scheme.JobsProcessScheme(zclient)
        gc_scheme = scheme.JobsGcScheme(zclient)

        job_id = control_scheme.add_job(self.func_version, self.func_name, self.func, self.func_kwargs)
        assert len(control_scheme.get_job_info(job_id)) > 0
        assert not process_scheme.is_deleted_job(job_id)

        ready_job = next(process_scheme.get_ready_jobs())
        assert job_id == ready_job.job_id
        process_scheme.associate_job(job_id)

        gc_scheme.remove_job_data(job_id)
        assert control_scheme.get_job_info(job_id) is None

    def test_get_job_info_none(self, zclient):
        control_scheme = scheme.JobsControlScheme(zclient)
        assert control_scheme.get_job_info("foobar") is None

    def test_process_ok(self, zclient):
        self._test_process(zclient, ok=True, with_save=False)

    def test_process_failed(self, zclient):
        self._test_process(zclient, ok=False, with_save=False)

    def test_process_with_save_ok(self, zclient):
        self._test_process(zclient, ok=True, with_save=True)

    def test_process_with_save_failed(self, zclient):
        self._test_process(zclient, ok=False, with_save=True)

    def _test_process(self, client, ok, with_save):
        assert scheme.init(client)
        control_scheme = scheme.JobsControlScheme(client)
        process_scheme = scheme.JobsProcessScheme(client)
        gc_scheme = scheme.JobsGcScheme(client)

        job_id = control_scheme.add_job(self.func_version, self.func_name, self.func, self.func_kwargs)
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        assert control_scheme.get_jobs_list() == [job_id]

        job_info = control_scheme.get_job_info(job_id)
        self._assert_job_info_new(job_info)

        count = 0
        for ready_job in process_scheme.get_ready_jobs():
            assert ready_job.job_id == job_id
            assert ready_job.version == self.func_version
            assert ready_job.func == self.func
            assert ready_job.kwargs == self.func_kwargs
            assert ready_job.state is None

            job_info = control_scheme.get_job_info(job_id)
            self._assert_job_info_taken(job_info)

            process_scheme.associate_job(job_id)

            if with_save:
                process_scheme.save_job_state(job_id, b"fictive state", ["fictive", "stack"])
                job_info = control_scheme.get_job_info(job_id)
                self._assert_job_info_in_progress(job_info)

            if ok:
                process_scheme.done_job(ready_job.job_id, retval=True, exc=None)
            else:
                process_scheme.done_job(ready_job.job_id, retval=None, exc="Traceback (most recent call last):\n")

            job_info = control_scheme.get_job_info(job_id)
            self._assert_job_info_finished(job_info, ok)

            count += 1
        assert count == 1

        count = 0
        for (job_id, done) in gc_scheme.get_jobs(0):
            assert done
            gc_scheme.remove_job_data(job_id)
            control_scheme.delete_job(job_id)
            count += 1
        assert count == 1

        assert control_scheme.get_jobs_list() == []

    def _assert_job_info(self, job_info):
        assert job_info["version"] == self.func_version
        assert job_info["name"] == self.func_name
        assert job_info["kwargs"] == self.func_kwargs
        assert isinstance(job_info["created"], float)
        assert isinstance(job_info["number"], int)
        assert "state" not in job_info

    def _assert_job_info_new(self, job_info):
        self._assert_job_info(job_info)
        assert not job_info["locked"]
        assert job_info["taken"] is None
        assert job_info["finished"] is None
        assert "stack" not in job_info
        assert "retval" not in job_info
        assert "exc" not in job_info

    def _assert_job_info_taken(self, job_info):
        self._assert_job_info(job_info)
        assert job_info["locked"]
        assert isinstance(job_info["taken"], float)
        assert job_info["finished"] is None
        assert "stack" not in job_info
        assert "retval" not in job_info
        assert "exc" not in job_info

    def _assert_job_info_in_progress(self, job_info):
        self._assert_job_info(job_info)
        assert job_info["locked"]
        assert isinstance(job_info["taken"], float)
        assert job_info["finished"] is None
        assert "stack" in job_info
        assert "retval" not in job_info
        assert "exc" not in job_info

    def _assert_job_info_finished(self, job_info, ok):
        self._assert_job_info(job_info)
        assert not job_info["locked"]
        assert isinstance(job_info["taken"], float)
        assert isinstance(job_info["finished"], float)

        if ok:
            assert "retval" in job_info
            assert "exc" not in job_info
        else:
            assert "retval" not in job_info
            assert "exc" in job_info


class TestRulesScheme:
    def test_head_cycle(self, zclient):
        assert scheme.init(zclient)
        rules_scheme = scheme.RulesScheme(zclient)
        assert rules_scheme.get_head() is None
        for count in range(5):
            rules_scheme.set_head("foobar{}".format(count))
            assert rules_scheme.get_head() == "foobar{}".format(count)


class TestAppsStateScheme:
    def test_state_cycle(self, zclient):
        assert scheme.init(zclient)
        apps_state_scheme = scheme.AppsStateScheme(zclient)
        assert apps_state_scheme.get_full_state() == {}
        apps_state_scheme.set_state("xxx", "foo", 1)
        apps_state_scheme.set_state("xxx", "bar", 2)
        apps_state_scheme.set_state("yyy", "baz", 3)
        assert apps_state_scheme.get_full_state() == {
            "xxx": {
                "foo": 1,
                "bar": 2,
            },
            "yyy": {
                "baz": 3,
            },
        }
