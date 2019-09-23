import os
import pytest

from tempfile import mkdtemp


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
