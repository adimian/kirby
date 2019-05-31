"""
Functions related to virtualenv creation and script installation.
Nothing is safe here, proceed with caution.
"""
import os
import subprocess
import sys
from venv import EnvBuilder


def install_package(executable, env_dir, name):
    args = [executable, "-m", "pip", "install", "--prefix", env_dir, name]
    return subprocess.check_output(args, env={"VIRTUAL_ENV": env_dir})


def create_venv(directory, package_name):
    """
    create a new virtual environment and installs a package automatically

    :param directory: target directory where the package will be installed.
    :param package_name: name of the package
    :return: (environment Python executable, installation logs)
    """

    if sys.platform == "darwin" and hasattr(sys, "real_prefix"):
        os.environ["__PYVENV_LAUNCHER__"] = os.path.join(
            sys.real_prefix, "bin", "python3"
        )

    class KirbyEnvBuilder(EnvBuilder):
        def __init__(self, package_name, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.package_name = package_name
            self.env_executable = None

        def post_setup(self, context):
            super().post_setup(context)
            installation_log = install_package(
                executable=context.env_exe,
                env_dir=context.env_dir,
                name=self.package_name,
            )
            self.env_executable = context.env_exe
            self.installation_log = installation_log

    ev = KirbyEnvBuilder(
        with_pip=True,
        upgrade=False,
        clear=True,
        symlinks=False,
        package_name=package_name,
    )
    ev.create(directory)

    return ev.env_executable, ev.installation_log
