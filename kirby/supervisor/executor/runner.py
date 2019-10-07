import logging
import threading

from kirby.models import JobType
from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Runner:
    def __init__(self, queue):
        self.queue = queue

        self.executor = None
        self.job = None

        logger.debug("Starting Runner's thread")
        self._thread = threading.Thread(target=self.catch_and_raise_jobs)
        self._thread.start()

    def catch_and_raise_jobs(self):
        from kirby.api.ext.topic import NoMoreMessagesException

        try:
            for job_desc in self.queue:
                if job_desc["type"] != JobType.SCHEDULED:
                    continue
                self.job = parse_job_description(job_desc)
                logger.debug(f"A runner received the job : '{self.job.name}'")

                with Executor(self.job) as executor:
                    self.executor = executor
                    executor.raise_process()

        except NoMoreMessagesException:
            logger.debug(
                f"The jobs' queue (which was run in test mode) "
                "has no jobs anymore"
            )

    @property
    def status(self):
        if self.executor:
            return self.executor.status
        else:
            return ProcessState.STOPPED

    def kill(self):
        if self.executor._process:
            self.executor._process.kill()
