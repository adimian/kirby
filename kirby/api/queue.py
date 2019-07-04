from kafka import KafkaProducer, KafkaConsumer
import logging
import tenacity

from .ext import (
    Topic,
    kafka_retry_args,
    kirby_value_deserializer,
    kirby_value_serializer,
)
from .context import ctx

logger = logging.getLogger(__name__)


class Queue(Topic):
    def __init__(self, name, use_tls=True, raw_record=False, testing=False):
        self.name = name
        self.use_tls = use_tls
        self.raw_record = raw_record
        self.testing = testing
        self.init_kafka()
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting queue {self.name} in {mode} mode")

    @tenacity.retry(**kafka_retry_args)
    def init_kafka(self):
        if self.testing:
            self._messages = []
        else:
            bootstrap_servers = ctx.KAFKA_BOOTSTRAP_SERVERS
            kafka_args = {"bootstrap_servers": bootstrap_servers}

            if self.use_tls:
                kafka_args.update(
                    {
                        "ssl_cafile": ctx.KAFKA_SSL_CAFILE,
                        "ssl_certfile": ctx.KAFKA_SSL_CERTFILE,
                        "ssl_keyfile": ctx.KAFKA_SSL_KEYFILE,
                        "security_protocol": "SSL",
                    }
                )
            logger.debug(f"kafka args: {kafka_args}")

            self._producer = KafkaProducer(
                value_serializer=kirby_value_serializer, **kafka_args
            )

            self._consumer = KafkaConsumer(
                self.name,
                group_id=ctx.KIRBY_SUPERVISOR_GROUP_ID,
                enable_auto_commit=True,
                value_deserializer=kirby_value_deserializer,
                **kafka_args,
            )
            self._consumer.poll()

    def append(self, *args, **kargs):
        super().send(*args, **kargs)

    def last(self):
        if self.testing:
            _, msg = self._messages[-1]
            return msg
        else:
            raise NotImplementedError("this is only for testing")
