import logging
import os
from enum import Enum
from os.path import expanduser

import attr
from smart_getenv import getenv

from .envbuilder import configure_env_builder, install_package

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


class ProcessState(Enum):
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


@attr.s
class Watcher:
    type = attr.ib(type=str)
    package = attr.ib(type=str)
    version = attr.ib(type=str)
    notify_failure = attr.ib(type=bool)
    notify_retry = attr.ib(type=bool)
    env = attr.ib(type=dict)

    _state = attr.ib(type=str, default=ProcessState.STOPPED)

    def venv_name(self):
        return f"kirby-{self.package}-{self.version}"

    def ensure_environment(self, kirby_venv_directory):

        process_venv = os.path.join(kirby_venv_directory, self.venv_name())

        builder = configure_env_builder(process_venv)

        if not os.path.exists(process_venv):
            context = builder.ensure_directories(process_venv)
            logging.info(
                f"creating venv for {self.venv_name()} at {process_venv}"
            )
            builder.create(process_venv)

            package_name = f"{self.package}=={self.version}"

            install_package(
                executable=context.env_exe,
                env_dir=process_venv,
                name=package_name,
            )
        else:
            context = builder.ensure_directories(process_venv)

        return context

    def run(self):
        kirby_venv_directory = getenv(
            "KIRBY_VENV_DIRECTORY", default=expanduser("~/.kirby/virtualenvs")
        )

        logger.debug(f"base virtualenv directory: {kirby_venv_directory}")
        self.ensure_environment(kirby_venv_directory)

    def status(self):
        return self._state
