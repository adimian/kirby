import multiprocessing

from kafka import KafkaConsumer
from smart_getenv import getenv

from kirby.supervisor.executor import Executor
from kirby.supervisor.supervisor import Supervisor


STREAM_TOPIC_JOBS_DUE = getenv("STREAM_TOPIC_TASKS_DUE", type=str)


mp_context = multiprocessing.get_context("spawn")


def start_supervisor():
    Supervisor().run()


def start_executor():
    consumer_proxy = KafkaConsumer(STREAM_TOPIC_JOBS_DUE)
    for job in consumer_proxy:
        process = mp_context.Process(target=Executor, args=(job, job.context))
        process.start()
