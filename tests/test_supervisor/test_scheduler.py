import datetime
import os
import pytest

from kirby.exc import CoolDownException
from kirby.supervisor import MessageType


def test_scheduler_can_grab_jobs(data_dir, scheduler):
    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()

    jobs = scheduler.parse_jobs(content)

    assert isinstance(jobs, list)
    assert all(isinstance(job, str) for job in jobs)


def test_scheduler_queue_jobs(scheduler):
    scheduler.queue_job("hello world")
    assert scheduler.queue_job_offers.next() == "hello world"


def test_scheduler_does_not_queue_twice_within_wakeup_period(scheduler):
    date_1 = datetime.datetime(2000, 1, 1, 0, 0, 0)
    date_2 = datetime.datetime(2000, 1, 1, 0, 0, 20)

    scheduler.queue_job("hello world", now=date_1)
    with pytest.raises(CoolDownException):
        scheduler.queue_job("hello world", now=date_2)


def test_scheduler_can_queue_after_wakeup_period(scheduler):
    date_1 = datetime.datetime(2000, 1, 1, 0, 0, 0)
    date_2 = datetime.datetime(2000, 1, 1, 0, 0, 40)

    scheduler.queue_job("hello world", now=date_1)
    scheduler.queue_job("hello world", now=date_2)


def test_scheduler_get_running_arbiters_job(scheduler, custom_job_creator):
    job = MessageType.JOB.value
    update = MessageType.UPDATE.value
    done = MessageType.DONE.value
    queue = scheduler.queue_running_deamons

    job1 = custom_job_creator(package_name="job1").json_repr()
    job2 = custom_job_creator(package_name="job2").json_repr()
    job3 = custom_job_creator(package_name="job3").json_repr()
    job4 = custom_job_creator(package_name="job4").json_repr()

    messages = [
        {"message": job4, "headers": {"type": job}},
        {"message": "done", "headers": {"type": done}},
        {"message": "update", "headers": {"type": update}},
        {"message": job1, "headers": {"type": job}},
        {"message": job2, "headers": {"type": job}},
        {"message": "done", "headers": {"type": done}},
        {"message": job3, "headers": {"type": job}},
        {"message": job4, "headers": {"type": job}},
        {"message": "done", "headers": {"type": done}},
    ]
    for msg in messages:
        queue.append(**msg)

    assert scheduler.get_running_arbiters_job(
        nb_supervisors=2, ask_update=False
    ) == [job1, job2, job3, job4]
