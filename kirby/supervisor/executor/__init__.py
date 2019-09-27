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
    notifications = attr.ib(type=dict)
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
    def __init__(self, job, _virtualenv=None):
        self.type = job.type

        self.package_name = job.package_name
        self.version = job.package_version
        self.package = f"{self.package_name}=={self.version}"

        self.notifications = job.notifications

        if _virtualenv:
            self.__virtualenv = _virtualenv
        self.venv_name = f"kirby-{self.package_name}-{self.version}"
        self.venv_created = False
        self.env = job.variables

        self._process_return_value = None
        self._thread = None

    @property
    def virtualenv(self):
        if not hasattr(self, "_Executor__virtualenv"):
            logging.debug("Creating the venv")
            venv_path = os.path.join(
                getenv(
                    "KIRBY_VENV_DIRECTORY",
                    default=expanduser("~/.kirby/virtualenvs"),
                ),
                self.venv_name,
            )

            logging.info(f"creating venv for {self.venv_name} at {venv_path}")
            env = VirtualEnvironment(venv_path)

            logging.debug("Installing package")
            env.install(self.package_name)
            logging.debug("Package installed")
            self.__virtualenv = env
        return self.__virtualenv

    def raise_process(self):
        args = [
            os.path.join(self.virtualenv.path, "bin", "python"),
            "-m",
            self.package_name,
        ]
        logging.debug("Raising process")
        process = Popen(
            args,
            cwd=self.virtualenv.path,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.wait()
        logging.debug("Process ended")

        retcode = process.returncode
        stdout = process.stdout.read()
        stderr = process.stderr.read()

        logging.debug(stdout)
        logging.debug(stderr)

        self._process_return_value = ProcessReturnValues(
            retcode, stdout.decode("utf-8"), stderr.decode("utf-8")
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
