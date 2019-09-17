import os
import pytest
from tempfile import mkdtemp

from kirby.supervisor.arbiter import Arbiter, ProcessState
from kirby.models import JobType


@pytest.fixture()
def venv_directory():
    temp_dir = mkdtemp()
    os.environ["KIRBY_VENV_DIRECTORY"] = temp_dir
    return temp_dir


def test_it_generates_venv_name():
    arbiter = Arbiter(
        script_type=JobType.SCHEDULED,
        package_name="dummy",
        version="0.0.0.dev",
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    assert arbiter.venv_name == "kirby-dummy-0.0.0.dev"


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_INSTALL"),
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
def test_arbiter_can_ensure_virtualenv_creation(venv_directory):
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    arbiter = Arbiter(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    context = arbiter.ensure_environment(venv_directory)

    assert context.is_installed(os.getenv("DUMMY_PACKAGE_INSTALL"))


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_INSTALL"),
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
def test_arbiter_can_start_scheduled_process():
    if not os.getenv("PIP_INDEX_URL"):
        print(
            f"You haven't set any extra index for pip. "
            "Make sure the package exists"
        )

    arbiter = Arbiter(
        script_type=JobType.SCHEDULED,
        package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    arbiter.run()
    assert arbiter.status == ProcessState.RUNNING

    arbiter.join()
    assert arbiter.status == ProcessState.STOPPED


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_INSTALL"),
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
def test_arbiter_can_start_daemon_process():
    arbiter = Arbiter(
        script_type=JobType.DAEMON,
        package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    arbiter.run()
    assert arbiter.status == ProcessState.RUNNING

    arbiter.join()
    assert arbiter.status == ProcessState.STOPPED


# def test_arbiter_can_restart_daemon_process():
#     arbiter = Arbiter(
#         script_type=JobType.DAEMON,
#         package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     arbiter.run()
#     assert arbiter.status() == ProcessState.RUNNING
#
#
# def test_arbiter_reports_process_failure():
#     arbiter = Arbiter(
#         script_type=JobType.SCHEDULED,
#         package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     arbiter.run()
#     assert arbiter.status() == ProcessState.FAILED
#
#
# def test_arbiter_is_asynchronous():
#     arbiter = Arbiter(
#         script_type=JobType.SCHEDULED,
#         package_name=os.getenv("DUMMY_PACKAGE_INSTALL"),
#         version=os.getenv("DUMMY_PACKAGE_VERSION"),
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     arbiter.run()
#     assert arbiter.status() == ProcessState.RUNNING
#
#     arbiter.join()
#     assert arbiter.get_return_values()
