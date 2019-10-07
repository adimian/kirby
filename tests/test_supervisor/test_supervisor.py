import datetime

from smart_getenv import getenv

from kirby.supervisor import send_arbiters_job_if_needed, MessageType

TESTING = getenv("TESTING", type=bool, default=True)


class FakeArbiter:
    def __init__(self, job):
        self.job = job


def test_supervisor_send_arbiters_job_if_needed(
    queue_running_deamons, custom_job_creator
):
    last_update_message = None
    arbiters = [
        FakeArbiter(custom_job_creator(package_name=pkg_name))
        for pkg_name in ["package_name_a", "package_name_b", "package_name_c"]
    ]

    queue_running_deamons.append(
        "update", headers={"type": MessageType.UPDATE.value}
    )
    start = datetime.datetime.utcnow()

    send_arbiters_job_if_needed(
        queue_running_deamons, arbiters, last_update_message
    )
    end = datetime.datetime.utcnow()

    assert [m.value for m in queue_running_deamons.between(start, end)] == [
        arbiters[0].job.json_repr(),
        arbiters[1].job.json_repr(),
        arbiters[2].job.json_repr(),
    ]


def test_supervisor_update_last_update_message(
    queue_running_deamons, custom_job_creator
):
    from kirby.supervisor import MessageType

    last_update_message = None
    arbiters = [
        FakeArbiter(custom_job_creator(package_name=pkg_name))
        for pkg_name in ["package_name_a", "package_name_b", "package_name_c"]
    ]

    queue_running_deamons.append(
        "update", headers={"type": MessageType.UPDATE.value}
    )

    assert (
        send_arbiters_job_if_needed(
            queue_running_deamons, arbiters, last_update_message
        ).value
        == "update"
    )
