import logging

from kirby.supervisor.executor import ProcessState
from kirby.supervisor.executor.arbiter import Arbiter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def test_arbiter_job_reraised_if_failed(
    venv_mock, process_mock_failing, queue_job_offers_failing
):
    arbiter = Arbiter(queue_job_offers_failing)

    # Wait until the arbiter catch the job
    while not arbiter.jobs:
        pass
    executor = arbiter.executors[0]
    # Loop until the process fail
    while executor.status != ProcessState.FAILED:
        pass
    # Loop until the process is re-raised
    while executor.status == ProcessState.FAILED:
        pass

    assert executor.status == ProcessState.RUNNING

    arbiter.kill()
