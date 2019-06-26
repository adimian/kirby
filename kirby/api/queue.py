import msgpack
from kafka import KafkaProducer, KafkaConsumer
from smart_getenv import getenv
import logging
import tenacity

from .ext import Topic, kafka_retry_args

logger = logging.getLogger(__name__)


class Queue(Topic):
    def __init__(self, name, testing=False):
        super().__init__(name=name, testing=testing, kirby_app=None)

    @tenacity.retry(**kafka_retry_args)
    def init_kafka(self):
        if self.testing:
            self._messages = []
        else:
            bootstrap_servers = getenv(
                "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
            )
            kafka_args = {"bootstrap_servers": bootstrap_servers}

            ssl_security_protocol = getenv(
                "KAFKA_USE_SSL", type=bool, default=False
            )

            if ssl_security_protocol:
                kafka_args.update(
                    {
                        "ssl_cafile": getenv("KAFKA_SSL_CAFILE", type=str),
                        "ssl_certfile": getenv("KAFKA_SSL_CERTFILE", type=str),
                        "ssl_keyfile": getenv("KAFKA_SSL_KEYFILE", type=str),
                        "security_protocol": "SSL",
                    }
                )

            logger.debug(f"bootstrap servers: {bootstrap_servers}")

            self._producer = KafkaProducer(
                value_serializer=msgpack.dumps, **kafka_args
            )

            self._consumer = KafkaConsumer(
                self.name,
                group_id=getenv("KIRBY_SUPERVISOR_GROUP_ID", type=str),
                enable_auto_commit=True,
                value_deserializer=msgpack.loads,
                **kafka_args,
            )

    def append(self, *args, **kargs):
        super().send(*args, **kargs)

    def last(self):
        if self.testing:
            _, msg = self._messages[-1]
            return msg
        else:
            raise NotImplementedError("this is only for testing")
