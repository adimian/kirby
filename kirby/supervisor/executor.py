import json
import subprocess

import attr
from psutil import Popen


def convert_variables(data):
    export = {}
    for variable in data:
        export[variable["key"]] = variable["value"]
    return export


@attr.s(hash=True)
class JobDescription:
    name = attr.ib(type=str)
    environment = attr.ib(type=str)
    package_name = attr.ib(type=str)
    package_version = attr.ib(type=str)
    notifications = attr.ib(type=tuple)
    variables = attr.ib(type=dict, convert=convert_variables)


def parse_job_description(job_description):
    kwargs = json.loads(job_description)
    job = JobDescription(**kwargs)

    return job


def execute_module(executable, package_name, env):
    args = [executable, "-m", package_name]
    with Popen(args, env=env, stdout=subprocess.PIPE) as process:
        process.wait()
        retcode = process.returncode
        output = process.stdout.read().decode("utf-8")

    return retcode, output
