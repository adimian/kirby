import os
import pytest

from unittest.mock import Mock
from tempfile import mkdtemp


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
def queue_failing(queue_job_offers, single_failing_job_description):
    queue_job_offers.send(single_failing_job_description)
    return queue_job_offers


def build_process_mock(mocker, return_code, sleep_time_for_wait=2):
    def wait_and_return():
        import time

        time.sleep(sleep_time_for_wait)
        return return_code

    process_mock_ = mocker.patch("psutil.Popen")
    process_mock_.return_value = Mock(
        wait=wait_and_return,
        poll=Mock(return_value=None),
        returncode=return_code,
    )
    return process_mock_


@pytest.fixture
def process_mock(mocker):
    return build_process_mock(mocker, return_code=0, sleep_time_for_wait=10)


@pytest.fixture
def process_mock_failing(mocker):
    return build_process_mock(mocker, return_code=1)


@pytest.fixture
def venv_mock(mocker):
    venv_mock_ = mocker.patch("virtualenvapi.manage.VirtualEnvironment")
    venv_dir = os.path.join("some", "path", "somewhere")
    venv_mock_.return_value = Mock(path=venv_dir)
    yield venv_mock_
