import datetime
import json

import requests
from smart_getenv import getenv

import logging

from ..exc import CoolDownException

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, queue, wakeup):
        self.queue = queue
        self.cooldown = datetime.timedelta(seconds=wakeup)

    def fetch_jobs(self):
        url = getenv("KIRBY_SCHEDULE_ENDPOINT", type=str)
        try:
            response = requests.get(url)
            return response.text
        except requests.exceptions.ConnectionError:
            logger.exception("unable to fetch jobs: ")

    def parse_jobs(self, content):
        jobs = []
        descriptions = json.loads(content)
        for description in descriptions["jobs"]:
            jobs.append(json.dumps(description))

        return jobs

    def queue_job(self, job, now=None):
        if now is None:
            now = datetime.datetime.utcnow()

        submitted_jobs = self.queue.between(start=now - self.cooldown, end=now)

        if job in submitted_jobs:
            raise CoolDownException()
        else:
            self.queue.append(job, submitted=now)
