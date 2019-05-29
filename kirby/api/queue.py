import msgpack
from kafka import KafkaProducer, KafkaConsumer
from smart_getenv import getenv
import logging

import datetime

logger = logging.getLogger(__name__)


class Queue:
    def __init__(self, name, testing=False):
        self.name = name
        self.testing = testing
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting queue {self.name} in {mode} mode")
        if testing:
            self.__messages = []
        else:
            bootstrap_servers = getenv(
                "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
            )

            logger.debug(f"bootstrap servers: {bootstrap_servers}")

            self.__producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=msgpack.dumps,
            )

    def append(self, message, submitted=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        if self.testing:
            self.__messages.append((submitted, message))

        else:
            self.__producer.send(self.name, message)

    def between(self, start, end):
        if self.testing:
            return [msg for t, msg in self.__messages if start <= t < end]
        else:
            raise NotImplementedError("not done yet")

    def last(self):
        if self.testing:
            _, msg = self.__messages[-1]
            return msg
        else:
            raise NotImplementedError("this is only for testing")
