import logging
import time

from smart_getenv import getenv

from kirby.models import JobType
from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)
from kirby.supervisor.executor.runner import Runner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

WAIT_BETWEEN_RETRIES = getenv(
    "KIRBY_WAIT_BETWEEN_RETRIES_EXT_CO", type=float, default=0.4
)


class Arbiter(Runner):
    def __init__(self, queue):
        super().__init__(queue)
        self._stop_signal = False

    def catch_and_raise_jobs(self):
        for job_desc in self.queue:
            while job_desc["type"] == JobType.DAEMON:
                break
        self.job = parse_job_description(job_desc)
        logger.debug(f"An arbiter received the job : '{self.job.name}'")

        with Executor(self.job) as executor:
            self.executor = executor
            while not self._stop_signal:
                executor.raise_process()
                if executor.status == ProcessState.STOPPED:
                    logger.warning(
                        f"The {self.job.type} job : '{self.job.name}'"
                        "terminated correctly but it was not supposed to."
                    )
                elif executor.status == ProcessState.FAILED:
                    logger.error(
                        f"The {self.job.type} job : '{self.job.name}' failed."
                    )
                logger.error(
                    f"The arbiter is re-raising the process '{self.job.name}'."
                )
                time.sleep(WAIT_BETWEEN_RETRIES)

    def stop(self):
        self._stop_signal = True

    def kill(self):
        self.stop()
        super(Arbiter, self).kill()
