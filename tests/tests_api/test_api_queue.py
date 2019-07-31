import os
import datetime
import pytest
from smart_getenv import getenv

from kirby.api.queue import Queue


def test_it_can_create_a_queue():
    q = Queue("my-queue", testing=True)
    q.append("hello")
    assert q.last() == "hello"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_it_can_create_a_queue_integration(kafka_topic_factory):
    start = datetime.datetime(year=2019, month=7, day=18, hour=15, minute=39)
    offset = datetime.timedelta(seconds=5)

    with kafka_topic_factory("kirby-test-integration"):
        q = Queue(
            "kirby-test-integration",
            init_time=start - 4 * offset,
            use_tls=getenv("KAFKA_USE_TLS", type=bool, default=True),
        )

        q.append("too early", submitted=start - 2 * offset)
        q.append("hello world", submitted=start)
        q.append("too late", submitted=start + 2 * offset)

        messages = q.between(start, start + offset)

        assert messages == ["hello world"]
