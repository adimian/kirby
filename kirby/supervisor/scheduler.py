import attr
import json


def convert_variables(data):
    export = {}
    for variable in data:
        export[variable["key"]] = variable["value"]
    return export


@attr.s
class JobDescription:
    name = attr.ib(type=str)
    environment = attr.ib(type=str)
    package_name = attr.ib(type=str)
    package_version = attr.ib(type=str)
    notifications = attr.ib(type=list)
    variables = attr.ib(type=list, convert=convert_variables)


class Scheduler:
    def parse_jobs(self, content):
        jobs = []
        descriptions = json.loads(content)
        for description in descriptions["jobs"]:
            job = JobDescription(**description)
            jobs.append(job)

        return jobs
