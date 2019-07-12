import logging

from .ext import Topic
from .context import ctx

logger = logging.getLogger(__name__)


class Queue(Topic):
    def __init__(self, name, *args, **kargs):
        if not kargs.get("testing", False):
            kargs.update(group_id=ctx.KIRBY_SUPERVISOR_GROUP_ID)
        super().__init__(topic_name=name, *args, **kargs)

    def append(self, *args, **kargs):
        self.send(*args, **kargs)

    def last(self):
        if self.testing:
            _, msg = self._messages[-1]
            if not self.raw_records:
                msg = msg.value
            return msg
        else:
            raise NotImplementedError("this is only for testing")
