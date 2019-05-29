import os

import pytest

from kirby.api.queue import Queue
from kirby.exc import CoolDownException
from kirby.supervisor.scheduler import Scheduler
import datetime


def test_scheduler_can_grab_jobs(data_dir):
    scheduler = Scheduler(queue=None, wakeup=60)

    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()

    jobs = scheduler.parse_jobs(content)

    assert isinstance(jobs, list)
    assert all(isinstance(job, str) for job in jobs)


def test_scheduler_queue_jobs():
    queue = Queue(name="jobs-to-do", testing=True)

    scheduler = Scheduler(queue=queue, wakeup=60)

    scheduler.queue_job("hello world")

    assert queue.last() == "hello world"


def test_scheduler_does_not_queue_twice_within_wakeup_period():
    queue = Queue(name="jobs-to-do", testing=True)

    scheduler = Scheduler(queue=queue, wakeup=30)

    date_1 = datetime.datetime(2000, 1, 1, 0, 0, 0)
    date_2 = datetime.datetime(2000, 1, 1, 0, 0, 20)

    scheduler.queue_job("hello world", now=date_1)
    with pytest.raises(CoolDownException):
        scheduler.queue_job("hello world", now=date_2)


def test_scheduler_can_queue_after_wakeup_period():
    queue = Queue(name="jobs-to-do", testing=True)

    scheduler = Scheduler(queue=queue, wakeup=30)

    date_1 = datetime.datetime(2000, 1, 1, 0, 0, 0)
    date_2 = datetime.datetime(2000, 1, 1, 0, 0, 40)

    scheduler.queue_job("hello world", now=date_1)
    scheduler.queue_job("hello world", now=date_2)
