import logging
import os
import pytest

from pygit2 import Repository
from tempfile import mkdtemp

from kirby.supervisor.executor import parse_job_description


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

DUMMY_PACKAGE_NAME = "dummykirby"


def get_branch_name():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    kirby_dir = os.path.split(os.path.split(dir_path)[0])[0]
    branch_full_name = Repository(kirby_dir).head.name
    return branch_full_name.split("/")[-1]


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
def job_description(single_job_description):
    return parse_job_description(single_job_description)
