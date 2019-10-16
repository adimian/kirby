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
JOB_OFFERS_DAEMON_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_DAEMON_JOB_OFFERS",
    type=str,
    default=".kirby.job-offers.daemon",
)
JOB_OFFERS_SCHEDULED_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_SCHEDULED_JOB_OFFERS",
    type=str,
    default=".kirby.job-offers.scheduled",
)


def run_supervisor(name, window, wakeup):
    server = Redis()
    queue_arbiter = Queue(
        name=JOB_OFFERS_DAEMON_TOPIC_NAME, use_tls=USE_TLS, group_id=name
    )
    queue_runner = Queue(
        name=JOB_OFFERS_SCHEDULED_TOPIC_NAME,
        use_tls=USE_TLS,
        group_id=JOB_OFFERS_SCHEDULED_TOPIC_NAME,
    )

    scheduler = Scheduler(
        queue_daemon=queue_arbiter, queue_scheduled=queue_runner, wakeup=wakeup
    )

    runner = Runner(queue_runner)
    arbiter = Arbiter(queue_arbiter)

    def signal_handler(sig, frame):
        arbiter.terminate()
        runner.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                content = scheduler.fetch_jobs()
                if content is not None:
                    jobs = scheduler.parse_jobs(content)
                    for job in jobs:
                        if (
                            job["type"] == JobType.DAEMON.value
                            and job in arbiter.jobs
                        ):
                            continue
                        else:
                            scheduler.queue_job(job)
            else:
                logger.debug("not the leader, do nothing.")

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
