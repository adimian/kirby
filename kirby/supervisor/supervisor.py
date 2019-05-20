import time

from kafka import KafkaProducer
from smart_getenv import getenv

from kirby.supervisor.consensus import Consensus


STREAM_TOPIC_JOBS_DUE = getenv("STREAM_TOPIC_JOBS_DUE", type=str)


class Scheduler(object):
    def __init__(self):
        self.consensus = Consensus()
        self.producer = KafkaProducer()

    def get_due_jobs(self):
        return []

    def run(self):
        while True:
            if self.consensus.is_leader():
                for job in self.get_due_jobs():
                    # Add job to queue
                    self.producer.send(
                        STREAM_TOPIC_JOBS_DUE, job.value, job.key
                    )
                    # Update jobs' status
                    job.status = "WAITING FOR PICKUP"
                    job.save()

            time.sleep(self.consensus.time_to_live)


def start():
    """Interface to properly start a Scheduler"""
    supervisor = Scheduler()
    supervisor.run()
