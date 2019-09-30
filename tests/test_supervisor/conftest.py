import os
import pytest

from tempfile import mkdtemp

from kirby.supervisor.executor import parse_job_description


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
