import os
import multiprocessing
import datetime
import pytest
from smart_getenv import getenv

from kirby.api.context import ContextManager
from kirby.api.queue import Queue


def _load_config(q):
    from kirby.api.context import ctx

    assert ctx.HELLO == "WORLD"
    assert ctx.MYLIST == ["this", "is", "a", "list"]
    assert ctx["HELLO"]

    q.put(True)


def test_it_can_read_configuration():
    os.environ["HELLO"] = "WORLD"
    os.environ["MYLIST"] = "this:is:a:list"

    ContextManager(
        {"HELLO": {"type": str}, "MYLIST": {"type": list, "separator": ":"}}
    )

    from kirby.api.context import ctx

    assert ctx.HELLO == "WORLD"
    assert ctx.MYLIST == ["this", "is", "a", "list"]

    q = multiprocessing.Queue(maxsize=1)
    ps = multiprocessing.Process(target=_load_config, args=(q,))
    ps.start()

    assert q.get(block=True, timeout=2)


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
