import datetime
import json
import logging
import requests

from enum import Enum
from smart_getenv import getenv

from kirby.exc import CoolDownException

logger = logging.getLogger(__name__)


class MessageType(Enum):
    UPDATE = "update"
    JOB = "job"
    DONE = "done"


class Scheduler:
    def __init__(self, wakeup, queue_job_offers, queue_running_deamons):
        self.queue_job_offers = queue_job_offers
        self.queue_running_deamons = queue_running_deamons
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
        for description in descriptions["scripts"]:
            jobs.append(json.dumps(description))

        return jobs

    def queue_job(self, job, now=None):
        if now is None:
            now = datetime.datetime.utcnow()

        submitted_jobs = self.queue_job_offers.between(
            start=now - self.cooldown, end=now
        )

        if job in submitted_jobs:
            raise CoolDownException()
        else:
            self.queue_job_offers.append(job, submitted=now)

    def _ask_update_on_running_arbiters_job(self):
        self.queue_running_deamons.send(
            "update", headers={"type": MessageType.UPDATE.value}
        )

    def get_running_arbiters_job(
        self, nb_supervisors, ask_update=True, earlier_rewind=None
    ):
        if ask_update:
            self._ask_update_on_running_arbiters_job()

        nb_supervisors_done = 0
        packages = []
        for message in self.queue_running_deamons.rewind(
            earlier=earlier_rewind
        ):
            msg_type = message.headers["type"]
            if msg_type != MessageType.UPDATE.value:
                if msg_type == MessageType.DONE.value:
                    nb_supervisors_done += 1
                elif msg_type == MessageType.JOB.value:
                    packages.insert(0, message.value)
            else:
                if nb_supervisors_done != nb_supervisors:
                    logging.warning(
                        f"The list of running arbiters may be wrong: The "
                        "number of supervisors listed is not equal as the "
                        "number of arbiters announced."
                    )
                break

        return packages
