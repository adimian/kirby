import logging

from redis import Redis
from smart_getenv import getenv
from time import perf_counter, sleep

from kirby.models import JobType
from kirby.api.ext.topic import earliest_kafka_date
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


def run_supervisor(name, window, wakeup, nb_runner):
    server = Redis()

    queue_arbiters = Queue(
        name=JOB_OFFERS_TOPIC_NAME, use_tls=USE_TLS, group_id=".kirby.arbiters"
    )
    queue_runners = Queue(
        name=JOB_OFFERS_TOPIC_NAME, use_tls=USE_TLS, group_id=".kirby.runners"
    )
    queue_supervisor = Queue(
        name=JOB_OFFERS_TOPIC_NAME,
        use_tls=USE_TLS,
        group_id=f".kirby.supervisors.{name}",
        init_time=earliest_kafka_date(),
    )

    scheduler = Scheduler(queue=queue_supervisor, wakeup=wakeup)

    for i in range(nb_runner):
        Runner(queue_runners)

    running_deamons = []
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                if content is not None:
                    jobs = scheduler.parse_jobs(content)
                    for job in jobs:
                        if job.type == JobType.DAEMON:
                            if job not in running_deamons:
                                running_deamons.append(job)
                                Arbiter(queue_arbiters)
                            else:
                                continue
                        scheduler.queue_job(job)
            else:
                logger.debug("not the leader, raising needed arbiters")
                for job_offers in queue_supervisor.nexts():
                    if job_offers.type == JobType.DAEMON:
                        if job_offers not in running_deamons:
                            running_deamons.append(job_offers)
                            Arbiter(queue_arbiters)

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
