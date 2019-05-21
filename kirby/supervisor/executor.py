import logging

from kafka_handler import KafkaLogHandler


def start_executor_for_job(job):
    Executor(job).run()


class Executor(object):
    def __init__(self, job):
        self.job = job
        self.context = job.context
        self.raw_logs = self.context.get("WORKER_RAW_LOGS", False)

    def set_logging_configuration(self, topic, key=None, partition=None):
        handler = KafkaLogHandler(
            topic=topic,
            key=key,
            partition=partition,
            raw_logging=self.raw_logs,
        )

        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logging.info("Start logging {}.".format(""))

    def run(self):
        self.set_logging_configuration()
        # Detect worker
        # Create venv and/or switch to venv if it exists
        # Pipi nstall
        # Execute when done
