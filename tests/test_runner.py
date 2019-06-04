import os
from tempfile import mkdtemp

import pytest
import sys

from kirby.supervisor.envbuilder import create_venv
from kirby.supervisor.executor import execute_module


@pytest.mark.skipif(
    not os.getenv("DUMMY_PACKAGE_INSTALL"),
    reason=(
        "You must pass the name of a PyPi package "
        "to install with DUMMY_PACKAGE_INSTALL"
    ),
)
def test_runner_can_create_virtualenv():
    destination_directory = mkdtemp()
    executable, log = create_venv(
        destination_directory, package_name=os.getenv("DUMMY_PACKAGE_INSTALL")
    )

    assert executable.endswith(("python", "python3"))
    assert log


def test_runner_can_run_modules(dummies_dir):
    marker = "hello, world!"
    env = {"KIRBY_TEST_MARKER": marker, "PYTHONPATH": dummies_dir}

    code, output = execute_module(
        executable=sys.executable, package_name="dummy", env=env
    )

    assert output.strip() == marker
    assert code == 0


def test_runner_logs_to_kafka_topic():
    pass


def test_runner_returns_job_status_failure():
    pass


def test_runner_returns_job_status_success():
    pass


def test_runner_returns_job_status_running():
    pass


def test_runner_runs_triggered_jobs():
    pass
