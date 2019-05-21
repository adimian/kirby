import time

from kafka import KafkaProducer
from smart_getenv import getenv

from kirby.supervisor.consensus import Consensus


def start_scheduler():
    Scheduler().run()


class Scheduler(object):
    def __init__(self):
        self.consensus = Consensus()
        self.producer = KafkaProducer()
        self.stream_topic = getenv("STREAM_TOPIC_JOBS_DUE", type=str)

    def get_due_jobs(self):
        return []

    def run(self):
        while True:
            if self.consensus.is_leader():
                for job in self.get_due_jobs():
                    self.producer.send(self.stream_topic, job.value, job.key)

                    # Update job's status
                    job.status = "WAITING FOR PICKUP"
                    job.save()

            time.sleep(self.consensus.time_to_live)
