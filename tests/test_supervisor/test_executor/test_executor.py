import os
import pytest

from kirby.models import JobType
from kirby.supervisor.executor import (
    Executor,
    parse_job_description,
    ProcessState,
    ProcessExecutionError,
)


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


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_can_ensure_virtualenv_creation(
    venv_directory, job_description
):
    with Executor(job_description) as executor:
        assert executor.virtualenv.is_installed(job_description.package_name)


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_can_start_process_with_pip_installation(
    venv_directory, job_description
):
    with Executor(job_description) as executor:
        executor.run()
        while executor.status == ProcessState.SETTINGUP:
            pass
        assert executor.status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_raise_error_if_process_fails(
    venv_directory, failing_job_description
):
    with pytest.raises(ProcessExecutionError):
        executor = Executor(failing_job_description)
        executor.run()
        executor.join()


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_executor_is_asynchronous(venv_directory, job_description):
    with Executor(job_description) as executor:
        executor.run()
        while executor.status == ProcessState.SETTINGUP:
            pass
        assert executor.status == ProcessState.RUNNING

    assert executor.return_values
