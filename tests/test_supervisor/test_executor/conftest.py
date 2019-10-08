import os
import pytest

from tempfile import mkdtemp

from kirby.supervisor.executor.runner import Runner
from kirby.supervisor.executor.arbiter import Arbiter


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


@pytest.fixture
def queue(queue_job_offers, single_job_description):
    queue_job_offers.send(single_job_description)
    return queue_job_offers


@pytest.fixture
def kirby_runner(queue):
    with Runner(queue=queue) as runner:
        yield runner


@pytest.fixture
def kirby_arbiter(single_failing_job_description):
    with Arbiter(job=single_failing_job_description) as arbiter:
        yield arbiter
