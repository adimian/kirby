import logging

from .ext.topic import Topic

logger = logging.getLogger(__name__)


class Queue(Topic):
    def __init__(self, name, *args, **kargs):
        super().__init__(topic_name=name, *args, **kargs)

    def append(self, *args, **kargs):
        self.send(*args, **kargs)

    def last(self):
        if self.testing:
            _, msg = self.topic_config.messages[-1]
            if not self.topic_config.raw_records:
                msg = msg.value
            return msg
        else:
            raise NotImplementedError("this is only for testing")
