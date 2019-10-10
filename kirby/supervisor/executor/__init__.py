import attr
import json
import logging
import os
import psutil
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
    kwargs = json.loads(job_description)
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
        self.env.update(PACKAGE_NAME=self.package_name, ID=str(job.id))

        self._thread = None
        self._process = None
        self.return_values = None

        self.status = ProcessState.SETTINGUP

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
            env = virtualenvapi.manage.VirtualEnvironment(venv_path)

            logging.debug("Installing package")
            env.install(self.package_name)
            logging.debug("Package installed")
            self.__virtualenv = env
        return self.__virtualenv

    def create_venv(self):
        return self.virtualenv

    def raise_process(self):
        args = [
            os.path.join(self.virtualenv.path, "bin", "python"),
            "-m",
            self.package_name,
        ]
        logging.debug("Raising process")
        self._process = psutil.Popen(
            args,
            cwd=self.virtualenv.path,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.status = ProcessState.RUNNING
        return_code = self._process.wait()
        if return_code == 0:
            self.status = ProcessState.STOPPED
        else:
            self.status = ProcessState.FAILED
        logging.debug("Process ended")

        logging.debug(f"Process stdout: {self._process.stdout.read()}")
        logging.debug(f"Process stderr: {self._process.stderr.read()}")

        self.return_values = ProcessReturnValues(
            self._process.returncode,
            self._process.stdout.read(),
            self._process.stderr.read(),
        )

    def run(self, block=False):
        self._thread = threading.Thread(target=self.raise_process)
        self._thread.start()
        if block:
            self.join()

    def join(self, timeout_s=None):
        # If timeout_ms == None : join will block until the process is joined
        if not self._thread:
            raise RuntimeError("Cannot join an Executor that didn't start.")
        self._thread.join(timeout_s)

    def _safe_join(self):
        try:
            self.join()
        except RuntimeError as e:
            logging.warning(repr(e))

    def _exit(self):
        self._safe_join()
        # Delete the job's virtualenv in the end
        delattr(self, "_Executor__virtualenv")
        if self.return_values.return_code != 0:
            raise ProcessExecutionError(self.return_values.stderr)

    def terminate(self):
        if self._process:
            if self._process.poll() is None:
                self._process.terminate()
        self._exit()

    def kill(self):
        if self._process:
            self._process.kill()
        self._exit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
