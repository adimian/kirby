import json
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
def job_description_text(data_dir):
    with open(os.path.join(data_dir, "sample_single_job.txt"), "r") as f:
        job_description = f.read()
    return job_description


@pytest.fixture()
def failing_job_description_text(data_dir):
    with open(
        os.path.join(data_dir, "sample_single_failing_job.txt"), "r"
    ) as f:
        job_description = f.read()
    return job_description


@pytest.fixture()
def job_description_json(job_description_text):
    return json.loads(job_description_text)


@pytest.fixture()
def failing_job_description_json(failing_job_description_text):
    return json.loads(failing_job_description_text)


@pytest.fixture()
def job_description(job_description_json):
    return parse_job_description(job_description_json)


@pytest.fixture()
def failing_job_description(failing_job_description_json):
    return parse_job_description(failing_job_description_json)


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
def queue_job_offers_scheduled(
    kafka_topic_factory, is_in_test_mode, kafka_use_tls
):
    topic_name = "job-offers.scheduled"
    with kafka_topic_factory(topic_name):
        with Queue(
            name=topic_name, use_tls=kafka_use_tls, testing=is_in_test_mode
        ) as queue:
            yield queue


@pytest.fixture
def queue_job_offers_daemon(
    kafka_topic_factory, is_in_test_mode, kafka_use_tls
):
    topic_name = "job-offers.daemon"
    with kafka_topic_factory(topic_name):
        with Queue(
            name=topic_name, use_tls=kafka_use_tls, testing=is_in_test_mode
        ) as queue:
            yield queue


@pytest.fixture
def scheduler(queue_job_offers_scheduled, queue_job_offers_daemon):
    return Scheduler(
        queue_daemon=queue_job_offers_daemon,
        queue_scheduled=queue_job_offers_scheduled,
        wakeup=30,
    )
