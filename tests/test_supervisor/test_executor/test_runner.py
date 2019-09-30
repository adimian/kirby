import logging
import os
import pytest

from kirby.supervisor.executor import ProcessState
from kirby.supervisor.executor.runner import Runner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_waits_for_jobs(
    venv_directory, queue_for_runner, job_description
):
    runner = Runner(_queue=queue_for_runner)
    assert runner.job == job_description


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_raise_job(venv_directory, queue_for_runner):
    runner = Runner(_queue=queue_for_runner)
    while runner.status != ProcessState.RUNNING:
        pass
    assert runner.status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_kill_job(venv_directory, queue_for_runner):
    runner = Runner(_queue=queue_for_runner)

    # Wait until the process started
    while runner.status != ProcessState.RUNNING:
        pass

    runner.kill()

    # Wait until the process is killed
    while runner.status == ProcessState.RUNNING:
        pass
    assert runner.status == ProcessState.FAILED
