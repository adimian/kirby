import logging
import threading

from kirby.models import JobType
from kirby.api.ext.topic import NoMoreMessagesException
from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Runner(Executor):
    def __init__(self, queue):
        self.queue = queue
        self.job = None
        thread = threading.Thread(target=self.run)
        thread.start()
        self.status = ProcessState.STOPPED

    def run(self, block=True):
        try:
            for job in self.queue:
                job_parsed = parse_job_description(job)
                if job_parsed.type != JobType.SCHEDULED:
                    continue
                self.job = job_parsed
                super().__init__(self.job)
                logger.debug(f"A runner received the job : '{self.job.name}'")
                super().raise_process()
                super().terminate()

        except NoMoreMessagesException:
            logger.debug(
                f"The jobs' queue (which was run in test mode) "
                "has no jobs anymore"
            )
