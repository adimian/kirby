import pytest

from kirby.supervisor.watcher import Watcher, ProcessState
from kirby.models import JobType
import os

from tempfile import mkdtemp


def test_it_generates_venv_name():
    watcher = Watcher(
        type=JobType.SCHEDULED,
        package="dummy",
        version="0.0.0.dev",
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )
    assert watcher.venv_name() == "kirby-dummy-0.0.0.dev"


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
def test_watcher_can_ensure_virtualenv_creation():
    watcher = Watcher(
        type=JobType.SCHEDULED,
        package=os.getenv("DUMMY_PACKAGE_INSTALL"),
        version=os.getenv("DUMMY_PACKAGE_VERSION"),
        notify_failure=True,
        notify_retry=True,
        env={"KIRBY_TEST_MARKER": "hello, world!"},
    )

    env_root = mkdtemp()
    context = watcher.ensure_environment(env_root)

    for dirs in (context.env_dir, context.python_dir):
        assert os.path.isdir(dirs)


#
# def test_watcher_can_start_scheduled_process():
#     watcher = Watcher(
#         type=JobType.SCHEDULED,
#         package="dummy",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#
#     watcher.run()
#     assert watcher.status() == ProcessState.RUNNING
#
#
# def test_watcher_can_start_daemon_process():
#     watcher = Watcher(
#         type=JobType.DAEMON,
#         package="dummy",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     watcher.run()
#     assert watcher.status() == ProcessState.RUNNING
#
#
# def test_watcher_can_restart_daemon_process():
#     watcher = Watcher(
#         type=JobType.DAEMON,
#         package="dummy-broken",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     watcher.run()
#     assert watcher.status() == ProcessState.RUNNING
#
#
# def test_watcher_reports_process_failure():
#     watcher = Watcher(
#         type=JobType.SCHEDULED,
#         package="dummy-broken",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     watcher.run()
#     assert watcher.status() == ProcessState.FAILED
#
#
# def test_watcher_is_asynchronous():
#     watcher = Watcher(
#         type=JobType.SCHEDULED,
#         package="dummy",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     watcher.run()
#     assert watcher.status() == ProcessState.RUNNING
#
#     watcher = Watcher(
#         type=JobType.SCHEDULED,
#         package="dummy",
#         version="0.0.0.dev",
#         notify_failure=True,
#         notify_retry=True,
#         env={"KIRBY_TEST_MARKER": "hello, world!"},
#     )
#     watcher.run()
#     assert watcher.status() == ProcessState.RUNNING
