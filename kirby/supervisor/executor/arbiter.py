import logging
import time

from smart_getenv import getenv

from kirby.supervisor.executor import Executor, ProcessState
from kirby.supervisor.executor.runner import Runner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

WAIT_BETWEEN_RETRIES = getenv(
    "KIRBY_WAIT_BETWEEN_RETRIES_EXT_CO", type=float, default=0.4
)


class Arbiter(Runner):
    def __init__(self, queue):
        self._stop_signal = False
        super().__init__(queue)

    def raise_executor(self, job):
        executor = Executor(job)
        self.executors.append(executor)
        while not self._stop_signal:
            executor.run()
            if executor.status == ProcessState.STOPPED:
                logger.warning(
                    f"The {executor.job.type} job : '{executor.job.name}'"
                    "terminated correctly but it was not supposed to."
                )
            elif executor.status == ProcessState.FAILED:
                logger.error(
                    f"The {executor.job.type} job : '{executor.job.name}' failed."
                )
            logger.error(
                f"The arbiter is re-raising the process '{executor.job.name}'."
            )
            time.sleep(WAIT_BETWEEN_RETRIES)

    def terminate(self):
        self._stop_signal = True
        super().terminate()

    def kill(self):
        self._stop_signal = True
        super().kill()
