from kirby.supervisor.scheduler import Scheduler
import os


def test_scheduler_can_grab_jobs(data_dir):
    scheduler = Scheduler()

    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()

    jobs = scheduler.parse_jobs(content)
    job = jobs[0]

    assert job.name == "Fetch bakery realtime sales"
    assert job.environment == "Development"
    assert job.package_version == "2.0.1"
    assert job.variables == {
        "SENTRY_DSN": "http://sentry.dsn.somewhere",
        "SSH_USERNAME": "demo",
        "ENV": "dev",
        "SSH_SERVER": "dev.server.somewhere:22",
        "KAFKA_URL": "some.kafka.server:9999",
    }
