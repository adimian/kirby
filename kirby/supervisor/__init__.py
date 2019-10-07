import datetime
import logging

from redis import Redis
from smart_getenv import getenv
from time import perf_counter, sleep

from kirby.models import JobType
from kirby.api.ext.topic import earliest_kafka_date
from kirby.api.queue import Queue
from kirby.supervisor.election import Election
from kirby.supervisor.scheduler import Scheduler, MessageType
from kirby.supervisor.executor.runner import Runner
from kirby.supervisor.executor.arbiter import Arbiter

logger = logging.getLogger(__name__)

USE_TLS = getenv("KAFKA_USE_TLS", type=bool, default=False)
JOB_OFFERS_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)
RUNNING_DEAMONS_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)


def send_arbiters_job_if_needed(
    queue_list_arbiters, arbiters, last_update_message
):
    if last_update_message:
        start = last_update_message.timestamp
    else:
        start = earliest_kafka_date()

    end = datetime.datetime.utcnow()

    # Search for new_update_message
    new_update_message = None
    for message in queue_list_arbiters.rewind(earlier=start, latest=end):
        if message.headers["type"] == MessageType.UPDATE.value:
            new_update_message = message
            break

    if new_update_message:
        last_update_message = new_update_message
        for arbiter in arbiters:
            queue_list_arbiters.append(
                arbiter.job.json_repr(),
                headers={"type": MessageType.JOB.value},
            )

    return last_update_message


def run_supervisor(name, window, wakeup, nb_runner):
    server = Redis()

    queue_job_offers_arbiters = Queue(
        name=JOB_OFFERS_TOPIC_NAME, use_tls=USE_TLS, group_id=".kirby.arbiters"
    )
    queue_job_offers_runners = Queue(
        name=JOB_OFFERS_TOPIC_NAME, use_tls=USE_TLS, group_id=".kirby.runners"
    )
    queue_running_deamons = Queue(
        name=RUNNING_DEAMONS_TOPIC_NAME, use_tls=USE_TLS
    )

    scheduler = Scheduler(
        queue_job_offers=queue_job_offers_arbiters,
        queue_running_deamons=queue_running_deamons,
        wakeup=wakeup,
    )

    for i in range(nb_runner):
        Runner(queue_job_offers_runners)

    arbiters = []
    last_update_message = None
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                if content is not None:
                    jobs = scheduler.parse_jobs(content)
                    running_arbiters_job = scheduler.get_running_arbiters_job(
                        nb_supervisors
                    )
                    for job in jobs:
                        if job.type == JobType.SCHEDULED or (
                            job.type == JobType.DAEMON
                            and (job.package_name not in running_arbiters_job)
                        ):
                            if job.type == JobType.DAEMON:
                                arbiters.append(
                                    Arbiter(queue_job_offers_arbiters)
                                )
                            scheduler.queue_job(job)

            else:
                logger.debug("not the leader, do nothing")
                last_update_message = send_arbiters_job_if_needed(
                    queue_running_deamons, arbiters, last_update_message
                )

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
