# pylint: disable=R0904
# pylint: disable=W0212


import pickle

import pytest

from powny.core import context


# =====
_EXTRA = {"foo": "bar"}

@pickle.dumps
def _FUNC_OK(limit):  # pylint: disable=C0103
    for _ in range(limit):
        context.get_context().save()
    return "LIMIT: {}".format(limit)

@pickle.dumps
def _FUNC_FAILED():  # pylint: disable=C0103
    raise RuntimeError

@pickle.dumps
def _FUNC_FAILED_AFTER_SUCCESS():  # pylint: disable=C0103
    context.get_context().save()
    raise RuntimeError

@pickle.dumps
def _FUNC_GET_JOB_ID():  # pylint: disable=C0103
    return context.get_context().get_job_id()

@pickle.dumps
def _FUNC_GET_EXTRA():  # pylint: disable=C0103
    return context.get_context().get_extra()


def _run_func(job_id, func=None, kwargs=None, state=None):
    steps = []
    job_thread = context.JobThread(
        job_id=job_id,
        func=func,
        kwargs=kwargs,
        state=state,
        save_context=steps.append,
        extra=_EXTRA,
    )
    job_thread.start()
    job_thread.join()
    return steps


def _check_exc_step(job_id, step):
    assert step.job_id == job_id
    assert step.state is None
    assert step.stack_or_retval is None
    assert isinstance(step.exc, str)
    assert step.exc.startswith("Traceback (most recent call last):\n")
    assert step.done


# =====
def test_get_fake_context():
    try:
        context._fake_context = 1
        assert context.get_context() == 1
    finally:
        context._fake_context = None
    with pytest.raises(AssertionError):
        context.get_context()


def test_normal_process():
    test_name = "test_normal_process"
    steps = _run_func(test_name, func=_FUNC_OK, kwargs={"limit": 3})

    assert len(steps) == 4
    for step in steps[:3]:
        assert step.job_id == test_name
        assert step.state.startswith(b"\x80\x03c_continuation")
        assert isinstance(step.stack_or_retval, list)
        assert len(step.stack_or_retval) > 0
        assert step.exc is None
        assert not step.done

    step = steps[-1]
    assert step.job_id == test_name
    assert step.state.startswith(b"\x80\x03c_continuation")
    assert step.stack_or_retval == "LIMIT: 3"
    assert step.exc is None
    assert step.done


def test_restore():
    test_name = "test_restore"
    steps = _run_func(test_name, func=_FUNC_OK, kwargs={"limit": 3})
    assert len(steps) == 4
    saved_state = steps[1].state
    assert saved_state.startswith(b"\x80\x03c_continuation")

    steps = _run_func(test_name, state=saved_state)
    assert len(steps) == 2
    step = steps[-1]
    assert step.job_id == test_name
    assert step.state.startswith(b"\x80\x03c_continuation")
    assert step.stack_or_retval == "LIMIT: 3"
    assert step.exc is None
    assert step.done


def test_get_job_id():
    test_name = "test_get_job_id"
    steps = _run_func(test_name, func=_FUNC_GET_JOB_ID)
    assert len(steps) == 1
    assert steps[0].stack_or_retval == test_name
    assert steps[0].done


def test_get_extra():
    steps = _run_func("test_get_extra", func=_FUNC_GET_EXTRA)
    assert len(steps) == 1
    assert steps[0].stack_or_retval == _EXTRA
    assert steps[0].done


def test_init_func_failed():
    test_name = "test_init_func_failed"
    steps = _run_func(test_name, func=b"garbage")
    assert len(steps) == 1
    _check_exc_step(test_name, steps[0])


def test_init_state_failed():
    test_name = "test_init_state_failed"
    steps = _run_func(test_name, state=b"garbage")
    assert len(steps) == 1
    _check_exc_step(test_name, steps[0])


def test_failed():
    test_name = "test_failed"
    steps = _run_func(test_name, func=_FUNC_FAILED)
    assert len(steps) == 1
    _check_exc_step(test_name, steps[0])


def test_failed_after_success():
    test_name = "test_failed_after_success"
    steps = _run_func(test_name, _FUNC_FAILED_AFTER_SUCCESS)
    assert len(steps) == 2
    step = steps[0]
    assert step.job_id == test_name
    assert step.state.startswith(b"\x80\x03c_continuation")
    assert isinstance(step.stack_or_retval, list)
    assert len(step.stack_or_retval) > 0
    assert step.exc is None
    assert not step.done
    _check_exc_step(test_name, steps[1])
