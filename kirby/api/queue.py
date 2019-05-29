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
            self._messages = []
        else:
            bootstrap_servers = getenv(
                "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
            )

            logger.debug(f"bootstrap servers: {bootstrap_servers}")

            self._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=msgpack.dumps,
            )

            self._consumer = KafkaConsumer(
                self.name,
                group_id=getenv("KIRBY_SUPERVISOR_GROUP_ID", type=str),
                enable_auto_commit=True,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=msgpack.loads,
            )

    def append(self, message, submitted=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        if self.testing:
            self._messages.append((submitted, message))

        else:
            timestamp_ms = int(submitted.timestamp() * 1000)
            self._producer.send(self.name, message, timestamp_ms=timestamp_ms)
            self._producer.flush()

    def between(self, start, end):
        if self.testing:
            return [msg for t, msg in self._messages if start <= t < end]
        else:
            self._consumer.poll(timeout_ms=5000)

            partitions = self._consumer.assignment()

            start_mapping = {p: start.timestamp() for p in partitions}
            start_offsets = self._consumer.offsets_for_times(start_mapping)

            start_timestamp = start.timestamp() * 1000
            end_timestamp = end.timestamp() * 1000

            messages = []
            for partition, offsets in start_offsets.items():
                self._consumer.seek(partition=partition, offset=offsets.offset)

            records_by_partition = self._consumer.poll(timeout_ms=5000)

            for partition, records in records_by_partition.items():
                for record in records:
                    if start_timestamp <= record.timestamp < end_timestamp:
                        messages.append((record.timestamp, record.value))

            messages.sort(key=lambda x: x[0])
            return [v for t, v in messages]

    def last(self):
        if self.testing:
            _, msg = self._messages[-1]
            return msg
        else:
            raise NotImplementedError("this is only for testing")
