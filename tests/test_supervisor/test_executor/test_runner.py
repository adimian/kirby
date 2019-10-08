import logging
import os
import pytest

from kirby.supervisor.executor import ProcessState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_waits_for_jobs(venv_directory, job_description, kirby_runner):
    while not kirby_runner.job:
        pass
    assert kirby_runner.job.package_name == job_description.package_name


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_raise_job(venv_directory, kirby_runner):
    status = kirby_runner.status
    while status != ProcessState.RUNNING:
        status = kirby_runner.status
    assert status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_kill_job(venv_directory, kirby_runner):
    # Wait until the process started
    while kirby_runner.status != ProcessState.RUNNING:
        pass

    kirby_runner.kill()

    # Wait until the process is killed
    while kirby_runner.status == ProcessState.RUNNING:
        pass
    assert kirby_runner.status == ProcessState.FAILED
