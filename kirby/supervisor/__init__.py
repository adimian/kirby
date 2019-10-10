import logging
import signal
import sys

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


def run_supervisor(name, window, wakeup, nb_runner):
    server = Redis()
    queue = Queue(
        name=JOB_OFFERS_TOPIC_NAME,
        use_tls=USE_TLS,
        group_id=JOB_OFFERS_TOPIC_NAME,
    )
    queue_for_supervisor = Queue(
        name=JOB_OFFERS_TOPIC_NAME,
        use_tls=USE_TLS,
        group_id=f".kirby.supervisors.{name}",
    )

    scheduler = Scheduler(queue=queue, wakeup=wakeup)

    runners = [Runner(queue) for i in range(nb_runner)]

    def signal_handler(sig, frame):
        for daemon in running_daemons:
            daemon.terminate()
        for runner in runners:
            runner.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    running_daemons = []
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                if content is not None:
                    jobs = scheduler.parse_jobs(content)
                    for job in jobs:
                        if job["type"] == JobType.DAEMON.value:
                            if job not in running_daemons:
                                running_daemons.append(job)
                                Arbiter(job)
                            else:
                                continue
                        scheduler.queue_job(job)
            else:
                logger.debug("not the leader, raising needed arbiters")
                for job_offer in queue_for_supervisor.nexts():
                    if job_offer["type"] == JobType.DAEMON.value:
                        if job_offer not in running_daemons:
                            running_daemons.append(job_offer)
                            Arbiter(job_offer)

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
