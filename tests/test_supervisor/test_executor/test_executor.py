import os
import pytest

from unittest.mock import Mock

from kirby.models import JobType
from kirby.supervisor.executor import (
    Executor,
    parse_job_description,
    ProcessState,
    ProcessExecutionError,
)


@pytest.fixture
def process_mock(mocker):
    return_code = 0
    process_mock_ = mocker.patch("psutil.Popen")
    process_mock_.return_value = Mock(
        wait=Mock(return_value=return_code), returncode=return_code
    )
    yield process_mock_


@pytest.fixture
def venv_mock(mocker):
    venv_mock_ = mocker.patch("virtualenvapi.manage.VirtualEnvironment")
    venv_dir = os.path.join("some", "path", "somewhere")
    venv_mock_.return_value = Mock(path=venv_dir)
    yield venv_mock_


def wait_until(executor, state):
    while executor.status != state:
        pass


def wait_as_long_as(executor, state):
    while executor.status == state:
        pass


def test_executor_can_parse_job(single_job_description):

    job = parse_job_description(single_job_description)

    assert job.id == 1
    assert job.name == "Test package"
    assert job.type == JobType.DAEMON
    assert job.environment == "Development"
    assert job.package_name == "dummykirby"
    assert job.package_version == "0.0.0.dev"
    assert job.variables == {"KIRBY_TEST_MARKER": "Hello, world!"}
    assert job.notifications == [
        {
            "on_retry": False,
            "on_failure": True,
            "groups": [
                {"name": "Sysadmin", "emails": ["someone@somewhere.here"]}
            ],
        }
    ]


def test_it_generates_venv_name(venv_directory, job_description):
    executor = Executor(job_description)
    assert executor.venv_name == "kirby-dummykirby-0.0.0.dev"


def test_executor_can_ensure_virtualenv_creation(
    venv_mock, process_mock, job_description
):
    executor = Executor(job_description)
    executor.create_venv()
    venv_mock.return_value.install.assert_called_once_with(
        job_description.package_name
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_can_ensure_virtualenv_creation_integration(
    venv_directory, job_description
):
    with Executor(job_description) as executor:
        assert executor.virtualenv.is_installed(job_description.package_name)


def test_executor_can_start_process(venv_mock, process_mock, job_description):
    venv_dir = venv_mock.return_value.path

    with Executor(job_description) as executor:
        executor.run()
        wait_until(executor, ProcessState.STOPPED)
    process_mock.assert_called_once_with(
        [
            os.path.join(venv_dir, "bin", "python"),
            "-m",
            job_description.package_name,
        ],
        cwd=venv_dir,
        env=job_description.variables,
        stderr=-1,
        stdout=-1,
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_can_start_process_integration(
    venv_directory, job_description
):
    with Executor(job_description) as executor:
        executor.run()

        wait_as_long_as(executor, ProcessState.SETTINGUP)

        assert executor.status == ProcessState.RUNNING


def test_executor_raise_error_if_process_fails(
    venv_mock, process_mock, failing_job_description
):
    return_code = 1
    process_mock.return_value.wait.return_value = return_code
    process_mock.return_value.returncode = return_code
    with pytest.raises(ProcessExecutionError):
        with Executor(failing_job_description) as executor:
            executor.run()
            wait_until(executor, ProcessState.FAILED)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_raise_error_if_process_fails_integration(
    venv_directory, failing_job_description
):
    with pytest.raises(ProcessExecutionError):
        executor = Executor(failing_job_description)
        executor.run()
        executor.join()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_is_asynchronous_integration(venv_directory, job_description):
    with Executor(job_description) as executor:
        executor.run()
        wait_as_long_as(executor, ProcessState.SETTINGUP)
        assert executor.status == ProcessState.RUNNING

    assert executor.return_values
