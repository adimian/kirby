import logging
import os
import pytest

from smart_getenv import getenv

from kirby.api.queue import Queue
from kirby.supervisor.executor import ProcessState
from kirby.supervisor.executor.runner import Runner


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

RUNNER_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)


@pytest.fixture
def queue_for_runner(single_job_description):
    queue = Queue(RUNNER_TOPIC_NAME, testing=True)
    queue.send(single_job_description)
    return queue


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
