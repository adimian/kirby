import json
from smart_getenv import getenv
import requests


class Scheduler:
    def __init__(self, queue):
        self.queue = queue

    def fetch_jobs(self):
        url = getenv("KIRBY_SCHEDULE_ENDPOINT", type=str)
        response = requests.get(url)
        return response.text

    def parse_jobs(self, content):
        jobs = []
        descriptions = json.loads(content)
        for description in descriptions["jobs"]:
            jobs.append(json.dumps(description))

        return jobs

    def queue_job(self, job):
        self.queue.append(job)
