"""
Functions related to virtualenv creation and script installation.
Nothing is safe here, proceed with caution.
"""
import os
import subprocess
import sys
from venv import EnvBuilder
from logging import getLogger

logger = getLogger(__name__)


def install_package(executable, env_dir, name):
    logger.debug(f"installing {name} in {env_dir}")
    args = [executable, "-m", "pip", "install", "--prefix", env_dir, name]
    return subprocess.check_output(args, env={"VIRTUAL_ENV": env_dir})


def configure_env_builder(directory):

    # this is a small trick to enable venv creation when on macos
    # with homebrew-supplied python installation
    if sys.platform == "darwin" and hasattr(sys, "real_prefix"):
        os.environ["__PYVENV_LAUNCHER__"] = os.path.join(
            sys.real_prefix, "bin", "python3"
        )

    builder = EnvBuilder(
        with_pip=True, upgrade=False, clear=False, symlinks=False
    )

    return builder
