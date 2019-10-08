import logging
import os
import pytest

from kirby.supervisor.executor import ProcessState, ProcessExecutionError
from kirby.supervisor.executor.arbiter import Arbiter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_arbiter_raise_job(venv_directory, kirby_arbiter):
    while kirby_arbiter.status != ProcessState.RUNNING:
        pass
    assert kirby_arbiter.status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_arbiter_kill_job(venv_directory, kirby_arbiter):
    # Wait until the process started
    while kirby_arbiter.status != ProcessState.RUNNING:
        pass

    try:
        kirby_arbiter.kill()
    except ProcessExecutionError:
        pass

    # Wait until the process is killed
    while kirby_arbiter.status == ProcessState.RUNNING:
        pass
    assert kirby_arbiter.status == ProcessState.FAILED


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_arbiter_job_reraised_if_failed(
    venv_directory, single_failing_job_description
):
    with Arbiter(job=single_failing_job_description) as arbiter:

        # Loop until the process fail
        while arbiter.status != ProcessState.FAILED:
            pass

        # Loop until the process is re-raised
        while arbiter.status == ProcessState.FAILED:
            pass

        assert arbiter.status == ProcessState.RUNNING

        try:
            arbiter.kill()
        except ProcessExecutionError:
            pass
