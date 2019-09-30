import logging
from time import perf_counter
from time import sleep

from redis import Redis
from smart_getenv import getenv

from kirby.supervisor.executor.runner import Runner
from .election import Election
from .scheduler import Scheduler
from ..api.queue import Queue

logger = logging.getLogger(__name__)


def run_supervisor(name, window, wakeup, nb_runner, nb_arbiter):
    server = Redis()
    queue = Queue(
        name=getenv(
            "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
        )
    )
    scheduler = Scheduler(queue=queue, wakeup=wakeup)

    for i in range(nb_runner):
        Runner(queue=scheduler.queue)

    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                if content is not None:
                    jobs = scheduler.parse_jobs(content)
                    for job in jobs:
                        scheduler.queue_job(job)

            else:
                logger.debug("not the leader, do nothing")

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
