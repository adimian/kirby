import msgpack
from kafka import KafkaProducer, KafkaConsumer
from smart_getenv import getenv
import logging

from .ext import Topic

logger = logging.getLogger(__name__)


class Queue(Topic):
    def __init__(self, name, testing=False, security_protocol="SSL"):
        self.name = name
        self.testing = testing
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting queue {self.name} in {mode} mode")
        if testing:
            self._messages = []
        else:
            bootstrap_servers = getenv(
                "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
            )
            self._args = {"bootstrap_servers": bootstrap_servers}

            if security_protocol:
                self._args.update(
                    {
                        "ssl_cafile": getenv("KAFKA_SSL_CAFILE"),
                        "ssl_certfile": getenv("KAFKA_SSL_CERTFILE"),
                        "ssl_keyfile": getenv("KAFKA_SSL_KEYFILE"),
                        "security_protocol": "SSL",
                    }
                )

            logger.debug(f"bootstrap servers: {bootstrap_servers}")

            self._producer = KafkaProducer(
                value_serializer=msgpack.dumps, **self._args
            )

            self._consumer = KafkaConsumer(
                self.name,
                group_id=getenv("KIRBY_SUPERVISOR_GROUP_ID", type=str),
                enable_auto_commit=True,
                value_deserializer=msgpack.loads,
                **self._args,
            )

    def append(self, *args, **kargs):
        super().send(*args, **kargs)

    def last(self):
        if self.testing:
            _, msg = self._messages[-1]
            return msg
        else:
            raise NotImplementedError("this is only for testing")
