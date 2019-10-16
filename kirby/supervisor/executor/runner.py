import logging
import threading

from kirby.api.ext.topic import NoMoreMessagesException
from kirby.supervisor.executor import (
    parse_job_description,
    Executor,
    ProcessState,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Runner(threading.Thread):
    def __init__(self, queue):
        self.executors = []
        self.threads = []
        self.queue = queue
        super().__init__()
        self.start()

    @property
    def jobs(self):
        return [e.job for e in self.executors]

    def watch_threads(self):
        i = 0
        while i < len(self.threads):
            thread = self.threads[i]
            if thread.is_alive():
                thread.join()
                self.threads.pop(i)
            else:
                i += 1

    def run(self):
        try:
            for job in self.queue:
                job = parse_job_description(job)
                thread = threading.Thread(
                    target=self.raise_executor, args=(job,)
                )
                thread.start()
                self.threads.append(thread)
                self.watch_threads()
        except NoMoreMessagesException:
            pass

    def raise_executor(self, job):
        executor = Executor(job)
        self.executors.append(executor)
        logger.debug(f"Running the {executor.job.type} job : '{job.name}'")
        executor.run()
        if executor.status == ProcessState.FAILED:
            logger.error(
                f"The {executor.job.type} job : '{executor.job.name}' failed."
            )

    def terminate(self):
        for e in self.executors:
            e.terminate()

    def kill(self):
        for e in self.executors:
            e.kill()
