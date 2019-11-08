import attr
import logging
import os
import psutil
import sys
import subprocess
import threading
import virtualenvapi.manage

from collections import namedtuple
from enum import Enum
from os.path import expanduser
from smart_getenv import getenv

from kirby.models import JobType


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def convert_variables(data):
    return {variable["key"]: variable["value"] for variable in data}


@attr.s(hash=True)
class JobDescription:
    id = attr.ib(type=int)
    name = attr.ib(type=str)
    type = attr.ib(type=JobType)
    environment = attr.ib(type=str)
    package_name = attr.ib(type=str)
    package_version = attr.ib(type=str)
    notifications = attr.ib(type=dict)
    variables = attr.ib(type=dict, converter=convert_variables)

    def json_repr(self):
        vars_ = vars(self).copy()
        vars_["type"] = self.type.value
        return vars_


def parse_job_description(job_description):
    kwargs = job_description.copy()
    type_ = kwargs["type"]
    if type_ == "scheduled":
        kwargs["type"] = JobType.SCHEDULED
    elif type_ == "daemon":
        kwargs["type"] = JobType.DAEMON
    job = JobDescription(**kwargs)
    return job


class ProcessState(Enum):
    SETTINGUP = "setting-up"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


ProcessReturnValues = namedtuple(
    "ProcessReturnValues", ["return_code", "stdout", "stderr"]
)


class ProcessExecutionError(Exception):
    pass


class Executor(threading.Thread):
    def __init__(self, job, _virtualenv=None):
        self.job = job

        if _virtualenv:
            self.__virtualenv = _virtualenv
        self._process = None
        self.__return_values = None

        self.status = ProcessState.SETTINGUP
        self.exc_info = None
        super().__init__()

    @property
    def env_vars(self):
        env_vars_ = self.job.variables.copy()
        env_vars_.update(
            PACKAGE_NAME=self.job.package_name, ID=str(self.job.id)
        )
        return env_vars_

    @property
    def venv_name(self):
        return f"kirby-{self.job.package_name}-{self.job.package_version}"

    @property
    def package(self):
        return f"{self.job.package_name}=={self.job.package_version}"

    @property
    def virtualenv(self):
        if not hasattr(self, "_Executor__virtualenv"):
            logging.debug(f"Creating the venv {self.venv_name}")
            venv_path = os.path.join(
                getenv(
                    "KIRBY_VENV_DIRECTORY",
                    default=expanduser("~/.kirby/virtualenvs"),
                ),
                self.venv_name,
            )

            logging.info(f"creating venv for {self.venv_name} at {venv_path}")
            env = virtualenvapi.manage.VirtualEnvironment(venv_path)

            logging.debug(f"Installing package: {self.job.package_name}")
            env.install("wheel")
            env.install(self.job.package_name)
            self.__virtualenv = env
        return self.__virtualenv

    def create_venv(self):
        return self.virtualenv

    def run(self):
        try:
            args = [
                os.path.join(self.virtualenv.path, "bin", "python"),
                "-m",
                self.job.package_name,
            ]
            logging.debug("Raising process")
            self._process = psutil.Popen(
                args,
                cwd=self.virtualenv.path,
                env=self.env_vars,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.status = ProcessState.RUNNING
            return_code = self._process.wait()
            stdout = self._process.stdout.read()
            stderr = self._process.stderr.read()

            logging.debug("Process ended")
            logging.debug(f"Process returncode: {return_code}")
            logging.debug(f"Process stdout: {stdout}")
            logging.debug(f"Process stderr: {stderr}")

            self.__return_values = ProcessReturnValues(
                return_code, stdout, stderr
            )
            if return_code == 0:
                self.status = ProcessState.STOPPED
            else:
                self.status = ProcessState.FAILED
                raise ProcessExecutionError(stderr)
        except:
            self.exc_info = sys.exc_info()
            logging.debug(
                f"The executor of {self.job.package_name} "
                f"has caught error: {self.exc_info}"
            )

    def get_return_values(self):
        if self.exc_info:
            raise self.exc_info[1].with_traceback(self.exc_info[2])
        return self.__return_values

    def terminate(self):
        if self._process:
            if self._process.poll() is None:
                self._process.terminate()

    def kill(self):
        if self._process:
            self._process.kill()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
