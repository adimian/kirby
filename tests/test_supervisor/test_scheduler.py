import datetime
import os
import pytest

from unittest.mock import patch, MagicMock

from kirby.exc import CoolDownException


@pytest.fixture
def jobs_request_result(data_dir):
    with open(os.path.join(data_dir, "sample_jobs_request.txt"), "r") as f:
        content = f.read()
    return content


def test_scheduler_can_parse_jobs(jobs_request_result, scheduler):

    jobs = scheduler.parse_jobs(jobs_request_result)

    [print(type(job)) for job in jobs]
    assert all(isinstance(job, dict) for job in jobs)


@patch("requests.get")
def test_scheduler_retrieve_jobs(get_mock, scheduler, jobs_request_result):
    os.environ[
        "KIRBY_SCHEDULE_ENDPOINT"
    ] = "http://a.webserver.somewhere/which_propose/schedule"

    get_mock.return_value = MagicMock(
        status_code=200, text=jobs_request_result
    )

    assert scheduler.fetch_jobs() == jobs_request_result


def test_scheduler_queue_jobs(scheduler):
    scheduler.queue_job("hello world")
    assert scheduler.queue.next() == "hello world"


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
