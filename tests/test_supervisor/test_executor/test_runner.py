import logging
import os
import pytest

from unittest.mock import Mock

from kirby.supervisor.executor import ProcessState
from kirby.supervisor.executor.runner import Runner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def test_runner_waits_for_jobs(
    process_mock_failing, venv_mock, queue, job_description
):
    runner = Runner(queue=queue)
    while not runner.jobs:
        pass
    assert runner.jobs[0] == job_description


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_runner_waits_for_jobs_integration(
    venv_directory, job_description, queue
):
    runner = Runner(queue=queue)
    while not runner.jobs:
        pass
    job = runner.jobs[0]
    assert job.package_name == job_description.package_name


def test_runner_raise_job(venv_mock, process_mock, queue):
    runner = Runner(queue=queue)

    while not runner.jobs:
        pass

    executor = runner.executors[0]
    status = executor.status
    while status != ProcessState.RUNNING:
        status = executor.status
    assert status == ProcessState.RUNNING


def test_runner_can_communicate_to_the_job(
    venv_mock, process_mock_failing, queue
):
    runner = Runner(queue=queue)
    while not runner.jobs:
        pass
    executor = runner.executors[0]

    # Wait until the process started
    while executor.status == ProcessState.SETTINGUP:
        pass

    runner.kill()
    while executor.status == ProcessState.RUNNING:
        pass

    assert executor.status == ProcessState.FAILED


class MockRunner:
    def __init__(self):
        self.threads = [
            Mock(name="1", is_alive=Mock(return_value=True), join=Mock()),
            Mock(name="2", is_alive=Mock(return_value=False), join=Mock()),
            Mock(name="3", is_alive=Mock(return_value=True), join=Mock()),
        ]

    def get_running_threads(self):
        return [thread for thread in self.threads if not thread.is_alive()]


def test_runner_is_watching_executors():
    runner = MockRunner()
    running_threads = runner.get_running_threads()
    Runner.watch_threads(runner)
    assert runner.threads == running_threads
