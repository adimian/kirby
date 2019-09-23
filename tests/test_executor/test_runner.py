from pytest import fixture
from smart_getenv import getenv

from kirby.api.testing import topic_sender
from kirby.supervisor.executor.runner import Runner

RUNNER_TOPIC_NAME = getenv(
    "KIRBY_TOPIC_JOB_OFFERS", type=str, default=".kirby.job-offers"
)


@fixture
def function_to_populates_queue(single_job_description):
    def populates_queue():
        with topic_sender() as send:
            send(RUNNER_TOPIC_NAME, single_job_description)

    return populates_queue


# def test_runner_waits_for_jobs(
#     single_job_description, function_to_populates_queue
# ):
#     runner = Runner()
#     function_to_populates_queue()
#     runner.package_name == "test_package_for_dev"
#
#
# def test_runner_is_asyncronous():
#     pass
#
#
# def test_runner_raise_job():
#     pass
#
#
# def test_runner_reports_process_failure():
#     pass
