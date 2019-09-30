import logging
import threading

from smart_getenv import getenv

from kirby.api.queue import Queue
from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

KAFKA_GROUP_ID = ".kirby.runners"


class Runner:
    def __init__(self, *args, _queue=None, **kargs):
        if not _queue:
            self.queue = Queue(
                name=getenv("KIRBY_TOPIC_JOB_OFFERS", type=str),
                group_id=KAFKA_GROUP_ID,
                *args,
                **kargs,
            )
        else:
            self.queue = _queue

        self.executor = None
        self.job = None

        logger.debug("Starting Runner's thread")
        self._thread = threading.Thread(target=self.catch_and_raise_jobs)
        self._thread.start()

    def catch_and_raise_jobs(self):
        from kirby.api.ext.topic import NoMoreMessagesException

        try:
            for job in self.queue:
                self.job = parse_job_description(job)
                logger.debug(f"A runner received the job : '{self.job.name}'")

                with Executor(self.job) as executor:
                    self.executor = executor
                    executor.run(block=True)

        except NoMoreMessagesException:
            logger.debug(
                f"The jobs' queue (wich was run in test mode) "
                "has no jobs anymore"
            )

    @property
    def status(self):
        if self.executor:
            return self.executor.status
        else:
            return ProcessState.STOPPED
