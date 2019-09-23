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
    assert job.name == "Fetch bakery realtime sales"
    assert job.type == "daemon"
    assert job.environment == "Development"
    assert job.package_version == "2.0.1"
    assert job.variables == {
        "SENTRY_DSN": "http://sentry.dsn.somewhere",
        "SSH_USERNAME": "demo",
        "ENV": "dev",
        "SSH_SERVER": "dev.server.somewhere:22",
        "KAFKA_URL": "some.kafka.server:9999",
    }


def test_it_generates_venv_name():
    executor = Executor(
        script_type=JobType.SCHEDULED,
        package_name="dummy",
        version="0.0.0.dev",
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    assert executor.venv_name == "kirby-dummy-0.0.0.dev"


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_NAME"),
    reason=(
        "You must pass the name of a PyPi package "
        "to install with DUMMY_PACKAGE_NAME"
    ),
)
@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_VERSION"),
    reason=(
        "You must pass the *exact* version of a PyPi package "
        "to install with DUMMY_PACKAGE_VERSION"
    ),
)
def test_executor_can_ensure_virtualenv_creation(venv_directory):
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    executor = Executor(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_NAME"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    context = executor.ensure_environment(venv_directory)

    assert context.is_installed(os.getenv("DUMMY_PACKAGE_NAME"))


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_NAME"),
    reason=(
        "You must pass the name of a PyPi package "
        "to install with DUMMY_PACKAGE_NAME"
    ),
)
@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_VERSION"),
    reason=(
        "You must pass the *exact* version of a PyPi package "
        "to install with DUMMY_PACKAGE_VERSION"
    ),
)
def test_executor_can_start_process_with_pip_installation(venv_directory):
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    executor = Executor(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_NAME"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    executor.run()
    assert executor.status == ProcessState.RUNNING


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_NAME"),
    reason=(
        "You must pass the name of a PyPi package "
        "to install with DUMMY_PACKAGE_INSTALL"
    ),
)
@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_VERSION"),
    reason=(
        "You must pass the *exact* version of a PyPi package "
        "to install with DUMMY_PACKAGE_VERSION"
    ),
)
def test_arbiter_raise_error_if_process_fails(venv_directory):
    with pytest.raises(ProcessExecutionError):
        with Executor(
            script_type=JobType.DAEMON,
            package_name=os.getenv("DUMMY_FAILING_PACKAGE_NAME"),
            version=os.getenv("DUMMY_FAILING_PACKAGE_VERSION"),
            notify_failure=True,
            notify_retry=True,
            env={"KIRBY_TEST_MARKER": "hello, world!"},
        ) as executor:
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
