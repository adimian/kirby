from kirby.supervisor.scheduler import Scheduler
from kirby.api.queue import Queue
import os


def test_scheduler_can_grab_jobs(data_dir):
    scheduler = Scheduler(queue=None)

    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()

    jobs = scheduler.parse_jobs(content)

    assert isinstance(jobs, list)
    assert all(isinstance(job, str) for job in jobs)


def test_scheduler_queue_jobs():
    queue = Queue(name="jobs-to-do", testing=True)

    scheduler = Scheduler(queue=queue)

    scheduler.queue_job("hello world")

    assert queue.last() == "hello world"
