import os
import pytest

from tempfile import mkdtemp
from smart_getenv import getenv

from kirby.api.queue import Queue
from kirby.supervisor.executor.runner import Runner

KIRBY_JOB_OFFERS_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)

TESTING = getenv("TESTING", type=bool, default=True)
KAFKA_USE_TLS = getenv("KAFKA_USE_TLS", type=bool, default=True)


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


@pytest.fixture
def queue_for_runner(single_job_description):
    queue = Queue(
        KIRBY_JOB_OFFERS_TOPIC_NAME, testing=TESTING, use_tls=KAFKA_USE_TLS
    )
    queue.send(single_job_description)
    return queue


@pytest.fixture
def runner(queue_for_runner):
    return Runner(queue=queue_for_runner)


@pytest.fixture
def queue_for_arbiter(single_failing_job_description):
    queue = Queue(
        KIRBY_JOB_OFFERS_TOPIC_NAME, testing=TESTING, use_tls=KAFKA_USE_TLS
    )
    queue.send(single_failing_job_description)
    return queue
