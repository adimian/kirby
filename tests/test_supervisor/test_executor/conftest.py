import os
import pytest

from tempfile import mkdtemp
from smart_getenv import getenv

from kirby.api.queue import Queue

KIRBY_JOB_OFFERS_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


@pytest.fixture
def queue_for_runner(single_job_description):
    queue = Queue(KIRBY_JOB_OFFERS_TOPIC_NAME, testing=True)
    queue.send(single_job_description)
    return queue


@pytest.fixture
def queue_for_arbiter(single_failing_job_description):
    queue = Queue(KIRBY_JOB_OFFERS_TOPIC_NAME, testing=True)
    queue.send(single_failing_job_description)
    return queue
