import os
import multiprocessing


def _load_config(q):
    from kirby.api.context import ctx

    assert ctx.HELLO == "WORLD"
    assert ctx.MYLIST == ["this", "is", "a", "list"]
    assert ctx["HELLO"]

    q.put(True)


def test_it_can_read_configuration():
    from kirby.api.context import ContextManager

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
