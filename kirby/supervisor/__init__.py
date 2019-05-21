import multiprocessing

from kafka import KafkaConsumer
from smart_getenv import getenv

from kirby.supervisor import executor, scheduler


STREAM_TOPIC_JOBS_DUE = getenv("STREAM_TOPIC_TASKS_DUE", type=str)


mp_context = multiprocessing.get_context("spawn")


def start_scheduler(amount=None):
    if amount:
        for i in range(0, int(amount)):
            process = mp_context.Process(target=scheduler.start_scheduler)
            process.start()
    else:
        scheduler.start_scheduler()


def start_executor():
    consumer_proxy = KafkaConsumer(STREAM_TOPIC_JOBS_DUE)
    for job in consumer_proxy:
        process = mp_context.Process(
            target=executor.start_executor, args=(job, job.context)
        )
        process.start()
