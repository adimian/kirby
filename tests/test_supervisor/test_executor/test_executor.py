import os
import pytest

from kirby.models import JobType
from kirby.supervisor.executor import (
    Executor,
    ProcessState,
    ProcessExecutionError,
)


def wait_until(executor, state):
    while executor.status != state:
        pass


def wait_as_long_as(executor, state):
    while executor.status == state:
        pass


def test_executor_can_parse_job(job_description):
    assert job_description.id == 1
    assert job_description.name == "Test package"
    assert job_description.type == JobType.DAEMON
    assert job_description.environment == "Development"
    assert job_description.package_name == "dummykirby"
    assert job_description.package_version == "0.0.0.dev"
    assert job_description.variables == {"KIRBY_TEST_MARKER": "Hello, world!"}
    assert job_description.notifications == [
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
        wait_until(executor, ProcessState.STOPPED)
    process_mock.assert_called_once_with(
        [
            os.path.join(venv_dir, "bin", "python"),
            "-m",
            job_description.package_name,
        ],
        cwd=venv_dir,
        env=executor.env_vars,
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

        wait_as_long_as(executor, ProcessState.SETTINGUP)

        assert executor.status == ProcessState.RUNNING


def test_executor_raise_error_if_process_fails(
    venv_mock, process_mock_failing, failing_job_description
):
    with pytest.raises(ProcessExecutionError):
        executor = Executor(failing_job_description)
        executor.start()
        wait_until(executor, ProcessState.FAILED)
        executor.get_return_values()


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
    executor = Executor(failing_job_description)
    executor.start()
    executor.join()
    with pytest.raises(ProcessExecutionError):
        executor.get_return_values()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_is_asynchronous_integration(venv_directory, job_description):
    executor = Executor(job_description)
    executor.start()
    executor.join()
    assert executor.get_return_values()


def test_executor_terminate_job(venv_mock, process_mock, job_description):
    executor = Executor(job_description)
    executor.start()
    wait_as_long_as(executor, ProcessState.SETTINGUP)

    executor.terminate()
    wait_as_long_as(executor, ProcessState.RUNNING)

    assert executor.status == ProcessState.STOPPED


def test_executor_kill_job(venv_mock, process_mock_failing, job_description):
    executor = Executor(job_description)
    executor.start()
    wait_as_long_as(executor, ProcessState.SETTINGUP)

    executor.kill()
    wait_as_long_as(executor, ProcessState.RUNNING)

    assert executor.status == ProcessState.FAILED
