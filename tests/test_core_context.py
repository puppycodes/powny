from powny.core import context

from .fixtures.context import run_in_context


# =====
def _func_ok(limit):
    for _ in range(limit):
        context.save_job_state()
    return "LIMIT: {}".format(limit)


def test_normal_process():
    result = run_in_context(_func_ok, {"limit": 3})
    assert len(result.steps) == 3
    for step in result.steps:
        assert step.state.startswith(b"\x80\x03c_continuation")
        assert isinstance(step.stack, list)
    assert result.end.retval == "LIMIT: 3"
    assert result.end.exc is None


def test_restore():
    result = run_in_context(_func_ok, {"limit": 3})
    assert len(result.steps) == 3
    assert result.end is not None
    job_id = result.steps[1].job_id
    state = result.steps[1].state

    result = run_in_context(state, job_id=job_id)
    assert len(result.steps) == 1
    assert result.end.retval == "LIMIT: 3"
    assert result.end.exc is None


def test_get_job_id():
    def func_get_job_id():
        return context.get_job_id()

    result = run_in_context(func_get_job_id)
    assert len(result.steps) == 0
    assert result.end.retval == result.end.job_id


def test_get_extra():
    def func_get_extra():
        return context.get_extra()

    result = run_in_context(func_get_extra, extra={"foo": "bar"})
    assert len(result.steps) == 0
    assert result.end.retval == {"foo": "bar"}


def test_init_func_failed():
    result = run_in_context(b"garbage", fatal=False)
    assert len(result.steps) == 0
    assert result.end.retval is None
    assert result.end.exc.startswith("Traceback (most recent call last):\n")


def test_failed():
    def func_failed():
        raise RuntimeError

    result = run_in_context(func_failed, fatal=False)
    assert len(result.steps) == 0
    assert result.end.retval is None
    assert result.end.exc.startswith("Traceback (most recent call last):\n")


def test_failed_after_success():
    def func_failed_after_success():
        context.save_job_state()
        raise RuntimeError

    result = run_in_context(func_failed_after_success, fatal=False)

    assert len(result.steps) == 1
    step = result.steps[0]
    assert step.state.startswith(b"\x80\x03c_continuation")
    assert isinstance(step.stack, list)

    assert result.end.retval is None
    assert result.end.exc.startswith("Traceback (most recent call last):\n")
