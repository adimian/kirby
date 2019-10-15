import datetime
import json
import logging
import requests

from smart_getenv import getenv

from kirby.models import JobType
from kirby.exc import CoolDownException

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, queue_daemon, queue_scheduled, wakeup):
        self.queue_daemon = queue_daemon
        self.queue_scheduled = queue_scheduled

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
        if job["type"] == JobType.DAEMON.value:
            queue = self.queue_daemon
        elif job["type"] == JobType.SCHEDULED.value:
            queue = self.queue_scheduled
        else:
            raise RuntimeError(
                f"The job to queue is neither"
                f" '{JobType.DAEMON.value}' nor '{JobType.SCHEDULED.value}'."
            )

        if now is None:
            now = datetime.datetime.utcnow()

        submitted_jobs = queue.between(start=now - self.cooldown, end=now)

        if job in submitted_jobs:
            raise CoolDownException()
        else:
            queue.append(job, submitted=now)
