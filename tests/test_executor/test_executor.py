import os
from kirby.supervisor.executor import parse_job_description


def test_executor_can_parse_job(data_dir):

    with open(os.path.join(data_dir, "sample_single_job.txt"), "r") as f:
        job_description = f.read()

    job = parse_job_description(job_description)

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
