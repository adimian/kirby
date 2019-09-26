import os
import pytest

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
    assert job.type == "daemon"
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
    with Executor(job_description) as executor:
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
        assert executor.status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("PIP_EXTRA_INDEX_URL"),
    reason=(
        f"You haven't set any extra index for pip. "
        "Make sure you host the package somewhere."
    ),
)
def test_arbiter_raise_error_if_process_fails(venv_directory, job_description):
    with pytest.raises(ProcessExecutionError):
        with Executor(job_description) as executor:
            executor.run()


# def test_executor_is_asynchronous():
#     executor = Executor(
#         script_type=JobType.SCHEDULED,
#         package_name=os.getenv("DUMMY_PACKAGE_NAME"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     executor.run()
#     assert executor.status() == ProcessState.RUNNING
#
#     executor.join()
#     assert executor.get_return_values()
