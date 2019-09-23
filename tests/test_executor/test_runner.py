import os
import pytest

from kirby.supervisor.executor import (
    Runner,
    ProcessState,
    ProcessExecutionError,
)
from kirby.models import JobType


def test_it_generates_venv_name():
    runner = Runner(
        script_type=JobType.SCHEDULED,
        package_name="dummy",
        version="0.0.0.dev",
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    assert runner.venv_name == "kirby-dummy-0.0.0.dev"


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
def test_runner_can_ensure_virtualenv_creation(venv_directory):
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    runner = Runner(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_NAME"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    context = runner.ensure_environment(venv_directory)

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
def test_runner_can_start_scheduled_process(venv_directory):
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    runner = Runner(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_NAME"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    runner.run()
    assert runner.status == ProcessState.RUNNING


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
def test_runner_can_start_daemon_process(venv_directory):
    runner = Runner(
        script_type=JobType.DAEMON,
        package_name=os.getenv("DUMMY_PACKAGE_NAME"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    runner.run()
    assert runner.status == ProcessState.RUNNING


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
        with Runner(
            script_type=JobType.DAEMON,
            package_name=os.getenv("DUMMY_FAILING_PACKAGE_NAME"),
            version=os.getenv("DUMMY_FAILING_PACKAGE_VERSION"),
            notify_failure=True,
            notify_retry=True,
            env={"KIRBY_TEST_MARKER": "hello, world!"},
        ) as runner:
            runner.run()


# def test_runner_can_restart_daemon_process():
#     runner = Runner(
#         script_type=JobType.DAEMON,
#         package_name=os.getenv("DUMMY_PACKAGE_NAME"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     runner.run()
#     assert runner.status() == ProcessState.RUNNING
#
#
# def test_runner_reports_process_failure():
#     runner = Runner(
#         script_type=JobType.SCHEDULED,
#         package_name=os.getenv("DUMMY_PACKAGE_NAME"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     runner.run()
#     assert runner.status() == ProcessState.FAILED
#
#
# def test_runner_is_asynchronous():
#     runner = Runner(
#         script_type=JobType.SCHEDULED,
#         package_name=os.getenv("DUMMY_PACKAGE_NAME"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     runner.run()
#     assert runner.status() == ProcessState.RUNNING
#
#     runner.join()
#     assert runner.get_return_values()
