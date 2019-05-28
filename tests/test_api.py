import os

from kirby.api.context import ContextManager
from kirby.api.queue import Queue
from multiprocessing import Process


def _load_config():
    from kirby.api.context import ctx

    assert ctx.HELLO == "WORLD"
    assert ctx.MYLIST == ["this", "is", "a", "list"]


def test_it_can_read_configuration():
    os.environ["HELLO"] = "WORLD"
    os.environ["MYLIST"] = "this:is:a:list"

    context_manager = ContextManager(
        {"HELLO": {"type": str}, "MYLIST": {"type": list, "separator": ":"}}
    )
    context_manager.load()

    from kirby.api.context import ctx

    assert ctx.HELLO == "WORLD"
    assert ctx.MYLIST == ["this", "is", "a", "list"]

    ps = Process(target=_load_config)
    ps.start()


def test_it_can_create_a_queue():
    q = Queue("my-queue", testing=True)
    q.append("hello")
    assert q.last() == "hello"
