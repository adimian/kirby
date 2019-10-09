import datetime
import json
import logging
import requests

from smart_getenv import getenv

from kirby.exc import CoolDownException

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, wakeup, queue):
        self.queue = queue
        self.cooldown = datetime.timedelta(seconds=wakeup)

    def fetch_jobs(self):
        url = getenv("KIRBY_SCHEDULE_ENDPOINT", type=str)
        try:
            response = requests.get(url)
            return response.text
        except requests.exceptions.ConnectionError as e:
            logger.exception(f"Unable to fetch jobs: {e}")

    def parse_jobs(self, content):
        return [description for description in json.loads(content)["scripts"]]

    def queue_job(self, job, now=None):
        if now is None:
            now = datetime.datetime.utcnow()

        submitted_jobs = self.queue.between(start=now - self.cooldown, end=now)

        if job in submitted_jobs:
            raise CoolDownException()
        else:
            self.queue.append(job, submitted=now)
