import msgpack
from kafka import KafkaProducer, KafkaConsumer
from smart_getenv import getenv
import logging

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

    def append(self, message):
        if self.testing:
            self.__messages.append(message)
        else:
            self.__producer.send(self.name, message)

    def last(self):
        if self.testing:
            return self.__messages[-1]
        else:
            raise NotImplementedError("this is only for testing")
