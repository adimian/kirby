import json


class Scheduler:
    def parse_jobs(self, content):
        jobs = []
        descriptions = json.loads(content)
        for description in descriptions["jobs"]:
            jobs.append(json.dumps(description))

        return jobs
