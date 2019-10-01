import logging
import os
import pytest

from kirby.supervisor.executor import ProcessState
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
def test_arbiter_job_reraised_if_failed(venv_directory, queue_for_arbiter):
    arbiter = Arbiter(_queue=queue_for_arbiter)

    # Loop until the process fail
    while arbiter.status != ProcessState.FAILED:
        pass

    # Loop until the process is re-raised
    while arbiter.status == ProcessState.FAILED:
        pass

    assert arbiter.status == ProcessState.RUNNING

    arbiter.stop()
