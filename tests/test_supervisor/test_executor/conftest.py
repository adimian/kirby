import os
import pytest

from tempfile import mkdtemp

from kirby.supervisor.executor.runner import Runner


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


@pytest.fixture
def queue_for_runner(queue_job_offers, single_job_description):
    queue_job_offers.send(single_job_description)
    return queue_job_offers


@pytest.fixture
def runner(is_in_test_mode, kafka_use_tls, queue_for_runner):
    return Runner(queue=queue_for_runner)


@pytest.fixture
def queue_for_arbiter(queue_job_offers, single_failing_job_description):
    queue_job_offers.send(single_failing_job_description)
    return queue_job_offers
