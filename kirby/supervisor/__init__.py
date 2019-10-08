import logging

from redis import Redis
from smart_getenv import getenv
from time import perf_counter, sleep

from kirby.models import JobType
from kirby.api.queue import Queue
from kirby.supervisor.election import Election
from kirby.supervisor.scheduler import Scheduler
from kirby.supervisor.executor.runner import Runner
from kirby.supervisor.executor.arbiter import Arbiter

logger = logging.getLogger(__name__)

USE_TLS = getenv("KAFKA_USE_TLS", type=bool, default=False)
JOB_OFFERS_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)
SUPERVISORS_KEY = "_SUPERVISORS"
SUPERVISORS_SET = "Supervisors"


def run_supervisor(name, window, wakeup, nb_runner):
    server = Redis()
    queue = Queue(
        name=JOB_OFFERS_TOPIC_NAME,
        use_tls=USE_TLS,
        group_id=JOB_OFFERS_TOPIC_NAME,
    )

    scheduler = Scheduler(queue=queue, wakeup=wakeup)

    for i in range(nb_runner):
        Runner(queue)

    # Add this supervisor to set
    server.sadd(SUPERVISORS_SET, name)

    try:
        running_deamons = []
        with Election(identity=name, server=server, check_ttl=window) as me:
            while True:
                checkpoint = perf_counter()
                if me.is_leader():
                    content = scheduler.fetch_jobs()
                    if content is not None:
                        jobs = scheduler.parse_jobs(content)
                        for job in jobs:
                            if job["type"] == JobType.DAEMON:
                                if job not in running_deamons:
                                    running_deamons.append(job)
                                    Arbiter(job)
                                else:
                                    continue
                            scheduler.queue_job(job)
                else:
                    logger.debug("not the leader, raising needed arbiters")
                    for job_offer in queue.nexts():
                        if job_offer["type"] == JobType.DAEMON:
                            if job_offer not in running_deamons:
                                running_deamons.append(job_offer)
                                Arbiter(job_offer)

                drift = perf_counter() - checkpoint
                next_wakeup = wakeup - drift
                logger.debug("waking up in {:.2f}s".format(next_wakeup))
                sleep(next_wakeup)
    finally:
        # remove from set
        server.srem(SUPERVISORS_SET, name)