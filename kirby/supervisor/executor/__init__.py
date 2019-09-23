import attr
import json
import logging
import os
import subprocess
import threading

from collections import namedtuple
from enum import Enum
from os.path import expanduser
from psutil import Popen
from smart_getenv import getenv
from virtualenvapi.manage import VirtualEnvironment

from .runner import Runner
from .arbiter import Arbiter


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


def convert_variables(data):
    return {variable["key"]: variable["value"] for variable in data}


@attr.s(hash=True)
class JobDescription:
    id = attr.ib(type=int)
    name = attr.ib(type=str)
    type = attr.ib(type=str)
    environment = attr.ib(type=str)
    package_name = attr.ib(type=str)
    package_version = attr.ib(type=str)
    notifications = attr.ib(type=tuple)
    variables = attr.ib(type=dict, converter=convert_variables)


def parse_job_description(job_description):
    kwargs = json.loads(job_description)
    job = JobDescription(**kwargs)
    return job


class ProcessState(Enum):
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


ProcessReturnValues = namedtuple(
    "ProcessReturnValues", ["return_code", "stdout", "stderr"]
)


class ProcessExecutionError(Exception):
    pass


class Executor:
    def __init__(
        self,
        script_type,
        package_name,
        version,
        notify_failure,
        notify_retry,
        env,
        _venv=None,
    ):
        self.type = script_type

        self.package_name = package_name
        self.version = version
        self.package = f"{self.package_name}=={self.version}"

        self.notify_failure = notify_failure
        self.notify_retry = notify_retry

        self._venv = _venv
        self.venv_name = f"kirby-{self.package_name}-{self.version}"
        self.venv_created = False
        self.env = env

        self._process_return_value = None
        self._thread = None

    def ensure_environment(self, venvs_directory=None):
        if self._venv:
            return self._venv
        else:
            if not venvs_directory:
                venvs_directory = getenv(
                    "KIRBY_VENV_DIRECTORY",
                    default=expanduser("~/.kirby/virtualenvs"),
                )
            venv_path = os.path.join(venvs_directory, self.venv_name)

            logging.info(f"creating venv for {self.venv_name} at {venv_path}")
            env = VirtualEnvironment(venv_path)

            env.install(self.package_name)
            return env

    def raise_process(self):
        venv = self.ensure_environment()

        args = [
            os.path.join(venv.path, "bin", "python"),
            "-m",
            self.package_name,
        ]
        process = Popen(
            args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        process.wait()

        retcode = process.returncode
        stdout = process.stdout.read().decode("utf-8")
        stderr = process.stderr.read().decode("utf-8")

        self._process_return_value = ProcessReturnValues(
            retcode, stdout, stderr
        )

    def run(self, block=False):
        self._thread = threading.Thread(target=self.raise_process)
        self._thread.start()
        if block:
            self.join()

    def get_return_values(self):
        return self._process_return_value

    def join(self):
        if self.status == ProcessState.RUNNING:
            self._thread.join()
            if self.get_return_values().return_code != 0:
                raise ProcessExecutionError(self._process_return_value.stderr)

    @property
    def status(self):
        if self._thread:
            if self._thread.is_alive():
                return ProcessState.RUNNING
            elif self.get_return_values().return_code != 0:
                return ProcessState.FAILED

        return ProcessState.STOPPED

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.join()
