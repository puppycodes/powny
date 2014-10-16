# pylint: disable=redefined-outer-name


import threading
import time

import pytest

from powny.core import (
    backends,
    tools,
)
from powny.backends.zookeeper import ifaces

from .fixtures.zookeeper import zclient  # pylint: disable=unused-import
zclient  # flake8 suppression pylint: disable=pointless-statement


# =====
class TestIfacesInit:
    def test_init(self, zclient):
        ifaces.init(zclient)
        ifaces.init(zclient)


class TestJobs:
    func_head = "0123456789abcdef"
    func_name = "method"
    func_state = b"pickled_function"
    func_kwargs = {"a": 1, "b": 2}

    def test_get_input_size(self, zclient):
        ifaces.init(zclient)
        control_iface = ifaces.JobsControl(zclient)
        assert control_iface.get_input_size() == 0
        for count in range(5):
            control_iface.add_job(self.func_head, self.func_name, self.func_kwargs, self.func_state)
            assert control_iface.get_input_size() == count + 1

    def test_delete_wait(self, zclient):
        ifaces.init(zclient)
        control_iface = ifaces.JobsControl(zclient)
        process_iface = ifaces.JobsProcess(zclient)
        gc_iface = ifaces.JobsGc(zclient)

        job_id = control_iface.add_job(self.func_head, self.func_name, self.func_kwargs, self.func_state)
        assert len(control_iface.get_job_info(job_id)) > 0
        assert not process_iface.is_deleted_job(job_id)

        ready_job = next(process_iface.get_ready_jobs())
        assert job_id == ready_job.job_id
        process_iface.associate_job(job_id)

        def remove_job():
            time.sleep(3)
            gc_iface.remove_job_data(job_id)

        remover = threading.Thread(target=remove_job)
        remover.daemon = True
        remover.start()

        before = time.time()
        with pytest.raises(backends.DeleteTimeoutError):
            control_iface.delete_job(job_id, timeout=1)
        control_iface.delete_job(job_id)
        assert time.time() - before >= 3
        assert control_iface.get_job_info(job_id) is None

    def test_remove_fresh_job(self, zclient):
        ifaces.init(zclient)
        control_iface = ifaces.JobsControl(zclient)
        process_iface = ifaces.JobsProcess(zclient)
        gc_iface = ifaces.JobsGc(zclient)

        job_id = control_iface.add_job(self.func_head, self.func_name, self.func_kwargs, self.func_state)
        assert len(control_iface.get_job_info(job_id)) > 0
        assert not process_iface.is_deleted_job(job_id)

        ready_job = next(process_iface.get_ready_jobs())
        assert job_id == ready_job.job_id
        process_iface.associate_job(job_id)

        gc_iface.remove_job_data(job_id)
        assert control_iface.get_job_info(job_id) is None

    def test_get_job_info_none(self, zclient):
        control_iface = ifaces.JobsControl(zclient)
        assert control_iface.get_job_info("foobar") is None

    def test_process_ok(self, zclient):
        self._test_process(zclient, ok=True, with_save=False)

    def test_process_failed(self, zclient):
        self._test_process(zclient, ok=False, with_save=False)

    def test_process_with_save_ok(self, zclient):
        self._test_process(zclient, ok=True, with_save=True)

    def test_process_with_save_failed(self, zclient):
        self._test_process(zclient, ok=False, with_save=True)

    def _test_process(self, client, ok, with_save):
        ifaces.init(client)
        control_iface = ifaces.JobsControl(client)
        process_iface = ifaces.JobsProcess(client)
        gc_iface = ifaces.JobsGc(client)

        job_id = control_iface.add_job(self.func_head, self.func_name, self.func_kwargs, self.func_state)
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        assert control_iface.get_jobs_list() == [job_id]

        job_info = control_iface.get_job_info(job_id)
        self._assert_job_info_new(job_info)

        count = 0
        for ready_job in process_iface.get_ready_jobs():
            assert ready_job.job_id == job_id
            assert ready_job.head == self.func_head
            assert ready_job.state == self.func_state

            job_info = control_iface.get_job_info(job_id)
            self._assert_job_info_taken(job_info)

            process_iface.associate_job(job_id)

            if with_save:
                process_iface.save_job_state(job_id, b"fictive state", ["fictive", "stack"])
                job_info = control_iface.get_job_info(job_id)
                self._assert_job_info_in_progress(job_info)

            if ok:
                process_iface.done_job(ready_job.job_id, retval=True, exc=None)
            else:
                process_iface.done_job(ready_job.job_id, retval=None, exc="Traceback (most recent call last):\n")

            job_info = control_iface.get_job_info(job_id)
            self._assert_job_info_finished(job_info, ok)

            count += 1
        assert count == 1

        count = 0
        for (job_id, done) in gc_iface.get_jobs(0):
            assert done
            gc_iface.remove_job_data(job_id)
            control_iface.delete_job(job_id)
            count += 1
        assert count == 1

        assert control_iface.get_jobs_list() == []

    def _assert_job_info(self, job_info):
        assert job_info["head"] == self.func_head
        assert job_info["method"] == self.func_name
        assert job_info["kwargs"] == self.func_kwargs
        assert isinstance(job_info["created"], str)
        assert isinstance(job_info["number"], int)

    def _assert_job_info_new(self, job_info):
        self._assert_job_info(job_info)
        assert job_info["locked"] is None
        assert job_info["taken"] is None
        assert job_info["finished"] is None
        assert job_info["stack"] is None
        assert job_info["retval"] is None
        assert job_info["exc"] is None

    def _assert_job_info_taken(self, job_info):
        self._assert_job_info(job_info)
        assert job_info["locked"] is not None
        assert isinstance(job_info["taken"], str)
        assert job_info["finished"] is None
        assert job_info["stack"] is None
        assert job_info["retval"] is None
        assert job_info["exc"] is None

    def _assert_job_info_in_progress(self, job_info):
        self._assert_job_info(job_info)
        assert job_info["locked"] is not None
        assert isinstance(job_info["taken"], str)
        assert job_info["finished"] is None
        assert isinstance(job_info["stack"], list)
        assert job_info["retval"] is None
        assert job_info["exc"] is None

    def _assert_job_info_finished(self, job_info, ok):
        self._assert_job_info(job_info)
        assert job_info["locked"] is None
        assert isinstance(job_info["taken"], str)
        assert isinstance(job_info["finished"], str)
        if ok:
            assert job_info["exc"] is None
        else:
            assert job_info["retval"] is None
            assert isinstance(job_info["exc"], str)


class TestRules:
    def test_head_cycle(self, zclient):
        ifaces.init(zclient)
        rules_iface = ifaces.Rules(zclient)
        assert rules_iface.get_head() is None
        for count in range(5):
            rules_iface.set_head("foobar{}".format(count))
            assert rules_iface.get_head() == "foobar{}".format(count)


class TestAppsState:
    def test_state_cycle(self, zclient):
        ifaces.init(zclient)
        apps_state_iface = ifaces.AppsState(zclient)

        assert apps_state_iface.get_full_state() == {}
        apps_state_iface.set_state("foo", 1)
        apps_state_iface.set_state("bar", 2)
        apps_state_iface.set_state("baz", 3)

        apps_state = apps_state_iface.get_full_state()
        node_name = tools.get_node_name()
        assert isinstance(apps_state["foo"][node_name], dict)
        assert isinstance(apps_state["bar"][node_name], dict)
        assert isinstance(apps_state["baz"][node_name], dict)


class TestCasStorage:
    def test_replace(self, zclient):
        ifaces.init(zclient)
        cas_storage = ifaces.CasStorage(zclient)

        with pytest.raises(backends.CasNoValueError):
            cas_storage.replace_value("/foo/bar")
        (old, write_ok) = cas_storage.replace_value("/foo/bar", default="test")
        assert old.value == "test"
        assert old.version is None
        assert write_ok is None

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=1, default=0)
        assert old.value == 0
        assert old.version is None
        assert write_ok is True

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=2, default=0)
        assert old.value == 1
        assert old.version is None
        assert write_ok is True

    def test_replace_versioned(self, zclient):
        ifaces.init(zclient)
        cas_storage = ifaces.CasStorage(zclient)

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=1, version=0, default=0)
        assert old.value == 0
        assert old.version is None
        assert write_ok is True

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=2, version=1, default=0)
        assert old.value == 1
        assert old.version == 0
        assert write_ok is True

        with pytest.raises(backends.CasVersionError):
            cas_storage.replace_value("/foo/bar", value=3, version=0, default=0)

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=3, version=0, default=0, fatal_write=False)
        assert old.value == 2
        assert old.version == 1
        assert write_ok is False

        (old, write_ok) = cas_storage.replace_value("/foo/bar", value=3, version=2, default=0)
        assert old.value == 2
        assert old.version == 1
        assert write_ok is True

    def test_get_set(self, zclient):
        ifaces.init(zclient)
        cas_storage = ifaces.CasStorage(zclient)

        with pytest.raises(backends.CasNoValueError):
            cas_storage.get_value("/foo/bar")

        result = cas_storage.get_value("/foo/bar", default="test")
        assert result.value == "test"
        assert result.version is None

        assert cas_storage.set_value("/foo/bar", value=1, version=0) is True
        result = cas_storage.get_value("/foo/bar")
        assert result.value == 1
        assert result.version == 0

        assert cas_storage.set_value("/foo/bar", value=2, version=0) is False

        assert cas_storage.set_value("/foo/bar", value=2, version=1) is True
        result = cas_storage.get_value("/foo/bar")
        assert result.value == 2
        assert result.version == 1
