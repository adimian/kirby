import logging
import os
import subprocess
import threading
from enum import Enum
from os.path import expanduser
from psutil import Popen
from smart_getenv import getenv
from virtualenvapi.manage import VirtualEnvironment


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


class ProcessState(Enum):
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


class Arbiter:
    def __init__(
        self,
        script_type,
        package_name,
        version,
        notify_failure,
        notify_retry,
        env,
    ):
        self.type = script_type

        self.package_name = package_name
        self.version = version
        self.package = f"{self.package_name}=={self.version}"

        self.notify_failure = notify_failure
        self.notify_retry = notify_retry

        self.venv_name = f"kirby-{self.package_name}-{self.version}"
        self.venv_created = False
        self.env = env

        self._process_return_value = None
        self._thread = None

    def ensure_environment(self, venvs_directory=None):
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
        process = Popen(args, env=self.env, stdout=subprocess.PIPE)
        process.wait()

        retcode = process.returncode
        output = process.stdout.read().decode("utf-8")

        self._process_return_value = retcode, output

    def run(self, block=False):
        self._thread = threading.Thread(target=self.raise_process)
        self._thread.start()
        if block:
            self.join()

    def get_return_values(self):
        return self._process_return_value

    def join(self):
        # TODO : Catch thread's errors
        if self.status == ProcessState.RUNNING:
            self._thread.join()

    @property
    def status(self):
        if self._thread:
            if self._thread.is_alive():
                return ProcessState.RUNNING
        return ProcessState.STOPPED
