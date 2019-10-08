import os
import pytest

from tempfile import mkdtemp

from kirby.models import JobType
from kirby.api.queue import Queue
from kirby.supervisor.executor import parse_job_description, JobDescription
from kirby.supervisor.scheduler import Scheduler


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


@pytest.fixture()
def single_job_description(data_dir):
    with open(os.path.join(data_dir, "sample_single_job.txt"), "r") as f:
        job_description = f.read()
    return job_description


@pytest.fixture()
def single_failing_job_description(data_dir):
    with open(
        os.path.join(data_dir, "sample_single_failing_job.txt"), "r"
    ) as f:
        job_description = f.read()
    return job_description


@pytest.fixture()
def job_description(single_job_description):
    return parse_job_description(single_job_description)


@pytest.fixture()
def failing_job_description(single_failing_job_description):
    return parse_job_description(single_failing_job_description)


@pytest.fixture()
def custom_job_creator():
    def create_job(
        id="1",
        name="Test job",
        type=None,
        environment="dev",
        package_name="dummykirby",
        package_version="0.0.0.dev",
        notifications=None,
        variables=None,
    ):
        type = type or JobType.SCHEDULED
        notifications = notifications or {}
        variables = variables or {}
        return JobDescription(
            id,
            name,
            type,
            environment,
            package_name,
            package_version,
            notifications,
            variables,
        )

    return create_job


@pytest.fixture
def queue_job_offers(kafka_topic_factory, is_in_test_mode, kafka_use_tls):
    topic_name = "job-offers"
    with kafka_topic_factory(topic_name):
        with Queue(
            name=topic_name, use_tls=kafka_use_tls, testing=is_in_test_mode
        ) as queue:
            yield queue


@pytest.fixture
def scheduler(queue_job_offers):
    return Scheduler(queue=queue_job_offers, wakeup=30)
