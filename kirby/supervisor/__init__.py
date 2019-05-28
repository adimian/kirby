from redis import Redis
from time import sleep
from .scheduler import Scheduler
from .election import Election
from ..api.queue import Queue
from time import perf_counter

import logging

logger = logging.getLogger(__name__)


def run_supervisor(name, window, wakeup):
    server = Redis()
    queue = Queue(name="job-offers")
    scheduler = Scheduler(queue=queue)
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                jobs = scheduler.parse_jobs(content)
                for job in jobs:
                    scheduler.queue_job(job)
            else:
                logger.debug("not the leader, do nothing")

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
