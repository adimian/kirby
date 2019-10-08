import logging
import threading
import time

from smart_getenv import getenv

from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

WAIT_BETWEEN_RETRIES = getenv(
    "KIRBY_WAIT_BETWEEN_RETRIES_EXT_CO", type=float, default=0.4
)


class Arbiter(Executor):
    def __init__(self, job):
        self.job = parse_job_description(job)
        self._stop_signal = False
        super().__init__(self.job)
        logger.debug(f"Running the daemon job : '{self.job.name}'")
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def run(self, block=True):
        while not self._stop_signal:
            super().raise_process()
            super().terminate()
            if self.status == ProcessState.STOPPED:
                logger.warning(
                    f"The {self.job.type} job : '{self.job.name}'"
                    "terminated correctly but it was not supposed to."
                )
            elif self.status == ProcessState.FAILED:
                logger.error(
                    f"The {self.job.type} job : '{self.job.name}' failed."
                )
            logger.error(
                f"The arbiter is re-raising the process '{self.job.name}'."
            )
            time.sleep(WAIT_BETWEEN_RETRIES)

    def terminate(self):
        self._stop_signal = True
        super().terminate()

    def kill(self):
        self._stop_signal = True
        super().kill()
