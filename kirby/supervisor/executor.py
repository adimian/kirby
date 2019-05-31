import json
import attr
from subprocess import check_output


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
    output = check_output([executable, "-m", package_name], env=env)
    return output.decode("utf-8")
