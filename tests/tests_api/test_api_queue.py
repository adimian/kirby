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
    offset = datetime.timedelta(seconds=5)

    with kafka_topic_factory("kirby-test-integration"):
        q = Queue(
            "kirby-test-integration",
            use_tls=getenv("KAFKA_USE_TLS", type=bool, default=True),
        )

        start = datetime.datetime.now()

        q.append("too early", submitted=start - offset)
        q.append("hello world", submitted=start + offset)
        q.append("too late", submitted=start + offset + offset)

        messages = q.between(start, start + (3 / 2) * offset)

        assert messages == ["hello world"]
