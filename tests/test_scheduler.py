from kirby.supervisor.scheduler import Scheduler

import os


def test_scheduler_can_grab_jobs(data_dir):
    scheduler = Scheduler()

    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()

    jobs = scheduler.parse_jobs(content)

    assert isinstance(jobs, list)
    assert all(isinstance(job, str) for job in jobs)
