import os
from tempfile import mkdtemp

import pytest
import sys

from kirby.supervisor.executor import execute_module


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
