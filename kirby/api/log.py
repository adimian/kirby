import os
import uuid

import __main__
from .ext.topic import Topic

LOGGER_TOPIC_NAME = "_logs"

LEVELS = ["critical", "error", "warning", "info", "debug", "noset"]
CORRESPONDENCES_VALUES_LEVELS = {
    "critical": 50,
    "error": 40,
    "warning": 30,
    "info": 20,
    "debug": 10,
    "noset": 0,
}


class Logger:
    # Logger is an adapter to a Topic
    # It is intended to imitate the behaviour of logger in the standard
    # library. There is 6 levels in the standard library:
    # CRITICAL  >   ERROR   >  WARNING  >   INFO    >   DEBUG   >   NOTSET

    def __init__(self, default_level="noset", **kargs):
        if default_level not in LEVELS:
            raise ValueError(
                f"The default_level given is not acceptable. "
                f"It must be one of {LEVELS}"
            )
        # Automatically assign a new group_id
        if not kargs.get("group_id"):
            kargs.update(group_id=str(uuid.uuid4()))
        self.logs_topic = Topic(LOGGER_TOPIC_NAME, **kargs)
        self.name = os.path.splitext(os.path.basename(__main__.__file__))[0]
        self.default_level = default_level

    def _send_log_factory(self, level):
        # Each time a level of log is called the factory is called to
        # create the right function to call.
        # To log with the default log level, the function log can be
        # called.
        if level == "log":
            level = self.default_level

        def send_log(message):
            self.logs_topic.send(
                message, headers={"level": level, "package_name": self.name}
            )

        return send_log

    def __getattr__(self, item):
        if item in [*LEVELS, "log"]:
            return self._send_log_factory(item)
        else:
            raise AttributeError(f"Logger has no attribute {item}")


class LogReader(Topic):
    def __init__(self, **kargs):
        topic_name = LOGGER_TOPIC_NAME
        # Automatically assign a new group_id
        if not kargs.get("group_id"):
            kargs.update(group_id=str(uuid.uuid4()))
        kargs.update(raw_records=True)
        super().__init__(topic_name, **kargs)

    def nexts(self, timeout_ms=500, package_name=None, max_records=None):
        # if max_records == None, the max_records will be set to
        # max_poll_records, which is set at KafkaConsumer init
        # https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.poll
        messages = super().__getattr__("nexts")(
            timeout_ms=timeout_ms, max_records=max_records
        )

        # Filter messages
        if messages:
            if package_name:
                messages = [
                    message
                    for message in messages
                    if message.headers["package_name"] == package_name
                ]
            return messages
        else:
            return []
