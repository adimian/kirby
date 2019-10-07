import logging
import threading
import time

from smart_getenv import getenv

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


class Arbiter:
    def __init__(self, job):
        self.job = parse_job_description(job)

        logger.debug("Starting Runner's thread")
        self._thread = threading.Thread(target=self.raise_job)
        self._thread.start()

    def raise_job(self):
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
        if self.executor._process:
            self.executor._process.kill()
