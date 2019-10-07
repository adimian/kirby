import datetime
import pytest

from smart_getenv import getenv

from kirby.api.queue import Queue
from kirby.supervisor import send_arbiters_job_if_needed, MessageType

TESTING = getenv("TESTING", type=bool, default=True)


class FakeExecutor:
    def __init__(self, package_name):
        self.package_name = package_name


class FakeArbiter:
    def __init__(self, executor):
        self.executor = executor


@pytest.fixture()
def queue_list_arbiters():
    return Queue(
        name=".kirby.list-arbiters", testing=TESTING, raw_records=True
    )


def test_supervisor_send_arbiters_job_if_needed(queue_list_arbiters):
    last_update_message = None
    arbiters = [
        FakeArbiter(FakeExecutor("package_name_a")),
        FakeArbiter(FakeExecutor("package_name_b")),
        FakeArbiter(FakeExecutor("package_name_c")),
    ]

    queue_list_arbiters.append(
        "update", headers={"type": MessageType.UPDATE.value}
    )
    start = datetime.datetime.utcnow()

    send_arbiters_job_if_needed(
        queue_list_arbiters, arbiters, last_update_message
    )
    end = datetime.datetime.utcnow()

    assert [m.value for m in queue_list_arbiters.between(start, end)] == [
        "package_name_a",
        "package_name_b",
        "package_name_c",
    ]


def test_supervisor_update_last_update_message(queue_list_arbiters):
    from kirby.supervisor import MessageType

    last_update_message = None
    arbiters = [
        FakeArbiter(FakeExecutor("package_name_a")),
        FakeArbiter(FakeExecutor("package_name_b")),
        FakeArbiter(FakeExecutor("package_name_c")),
    ]

    queue_list_arbiters.append(
        "update", headers={"type": MessageType.UPDATE.value}
    )

    assert (
        send_arbiters_job_if_needed(
            queue_list_arbiters, arbiters, last_update_message
        ).value
        == "update"
    )
