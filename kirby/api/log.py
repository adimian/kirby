import __main__
import os
import tenacity
from kafka import KafkaConsumer

from .queue import Queue
from .ext import kafka_retry_args, kirby_value_deserializer
from .context import ctx

LOGGER_TOPIC_NAME = "_logs"

LEVELS = ["critical", "error", "warning", "info", "debug", "noset"]


class Logger:
    # Logger is an adapter to a Queue
    # It is intended to imitate the behaviour of logger in the standard
    # library. There is 6 levels in the standard library:
    # CRITICAL  >   ERROR   >  WARNING  >   INFO    >   DEBUG   >   NOTSET

    def __init__(self, default_level="noset"):
        if default_level not in LEVELS:
            raise ValueError(
                f"The default_level given is not acceptable. "
                f"It must be one of {LEVELS}"
            )
        self.queue = Queue(LOGGER_TOPIC_NAME)
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
            self.queue.send(
                message, headers={"level": level, "package_name": self.name}
            )

        return send_log

    def __getattr__(self, item):
        if item in [*LEVELS, "log"]:
            return self._send_log_factory(item)
        else:
            raise AttributeError(f"Logger has no attribute {item}")


class LogReader(Queue):

    viewer = 0

    def __init__(self, use_tls=True):
        self.name = LOGGER_TOPIC_NAME
        self.testing = False
        self.raw_records = True

        self.group_id = f"LogReader_{LogReader.viewer}"
        self.kafka_args = {
            "bootstrap_servers": ctx.KAFKA_BOOTSTRAP_SERVERS,
            "value_deserializer": kirby_value_deserializer,
            "group_id": self.group_id,
        }

        if use_tls:
            self.kafka_args.update(
                {
                    "ssl_cafile": ctx.KAFKA_SSL_CAFILE,
                    "ssl_certfile": ctx.KAFKA_SSL_CERTFILE,
                    "ssl_keyfile": ctx.KAFKA_SSL_KEYFILE,
                    "security_protocol": "SSL",
                }
            )

        LogReader.viewer += 1

    @property
    def _consumer(self):
        if not hasattr(self, "_hidden_consumer"):
            self._hidden_consumer = tenacity.retry(**kafka_retry_args)(
                KafkaConsumer
            )(self.name, **self.kafka_args)
        return self._hidden_consumer

    def nexts(self, timeout_ms=500, package_name=None, max_records=None):
        # if max_records == None, the max_records will be set to
        # max_poll_records, which is set at KafkaConsumer init
        # https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.poll
        messages = super().nexts(timeout_ms, max_records=max_records)

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
