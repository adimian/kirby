import datetime
import logging
import msgpack
import tenacity
from collections import namedtuple
from contextlib import contextmanager
from functools import partial
from smart_getenv import getenv

from kafka import KafkaConsumer, KafkaProducer
from kafka.consumer.fetcher import ConsumerRecord
from kafka.errors import NoBrokersAvailable, NodeNotReadyError
from kafka.structs import OffsetAndTimestamp

from ..context import ctx

logger = logging.getLogger(__name__)

RETRIES = getenv("EXT_RETRIES", type=int, default=3)
WAIT_BETWEEN_RETRIES = getenv(
    "EXT_WAIT_BETWEEN_RETRIES", type=float, default=0.4
)
topic_retry_decorator = tenacity.retry(
    retry=(
        tenacity.retry_if_exception_type(NoBrokersAvailable)
        | tenacity.retry_if_exception_type(NodeNotReadyError)
    ),
    wait=tenacity.wait_fixed(WAIT_BETWEEN_RETRIES),
    stop=tenacity.stop_after_attempt(RETRIES),
    reraise=True,
)

TopicConfig = namedtuple(
    "TopicConfig", ["name", "group_id", "use_tls", "raw_records"]
)
TopicTestModeConfig = namedtuple(
    "TopicConfig", ["name", "cursor_position", "raw_records", "messages"]
)


kirby_value_deserializer = partial(msgpack.loads, raw=False)
kirby_value_serializer = msgpack.dumps


def parse_records(records_by_partition, raw_records=False):
    if records_by_partition:
        if raw_records:
            # The records are Namedtuple.
            # Namedtuple._replace return the same Namedtuple with the
            # values modified and let the original one untouched.
            return [
                record._replace(
                    headers={
                        k: kirby_value_deserializer(v)
                        for k, v in record.headers
                    }
                )
                for records in records_by_partition.values()
                for record in records
            ]
        else:
            return [
                record.value
                for records in records_by_partition.values()
                for record in records
            ]


def is_in_test_mode(topic_config):
    return isinstance(topic_config, TopicTestModeConfig)


def get_kafka_args(topic_config):
    if not is_in_test_mode(topic_config):
        kafka_args = {"bootstrap_servers": ctx.KAFKA_BOOTSTRAP_SERVERS}
        if topic_config.use_tls:
            kafka_args.update(
                {
                    "ssl_cafile": ctx.KAFKA_SSL_CAFILE,
                    "ssl_certfile": ctx.KAFKA_SSL_CERTFILE,
                    "ssl_keyfile": ctx.KAFKA_SSL_KEYFILE,
                    "security_protocol": "SSL",
                }
            )
        return kafka_args
    else:
        return {}


@contextmanager
def temporary_rollback(consumer, start):
    start_ts = start.timestamp() * 1000
    partitions = consumer.assignment()
    old_offsets = {
        partition: consumer.committed(partition) for partition in partitions
    }
    offsets_for_start = consumer.offsets_for_times(
        {p: start_ts for p in partitions}
    )
    new_offsets = {
        p: offset
        if offset
        else OffsetAndTimestamp(
            offset=consumer.highwater(p), timestamp=start_ts
        )
        for p, offset in offsets_for_start.items()
    }

    # Set offsets to start
    for partition, offsets in new_offsets.items():
        consumer.seek(partition=partition, offset=offsets.offset)

    yield

    # Rollback to the old offsets
    for partition, offsets in old_offsets.items():
        consumer.seek(partition=partition, offset=offsets)


class Consumer:
    def __init__(self, topic_config):
        self.topic_config = topic_config
        if not is_in_test_mode(topic_config):
            self._consumer = KafkaConsumer(
                self.topic_config.name,
                group_id=topic_config.group_id,
                value_deserializer=kirby_value_deserializer,
                **get_kafka_args(topic_config),
            )
            # Update metadata inside self._consumer
            self._consumer.partitions_for_topic(self.topic_config.name)

    @topic_retry_decorator
    def _get_nexts_kafka_records(self, timeout_ms, max_records):
        messages = self._consumer.poll(
            max_records=max_records, timeout_ms=timeout_ms
        )
        self._consumer.commit()
        return messages

    def next(self, timeout_ms=500):
        messages = self.nexts(timeout_ms=timeout_ms, max_records=1)
        if messages:
            return messages[0]
        else:
            return None

    def nexts(self, timeout_ms=500, max_records=None):
        if not is_in_test_mode(self.topic_config):
            return parse_records(
                self._get_nexts_kafka_records(timeout_ms, max_records),
                raw_records=self.topic_config.raw_records,
            )
        else:
            if self.topic_config.messages:
                start = self.topic_config.cursor_position
                end = self.topic_config.cursor_position + max_records
                self.topic_config = self.topic_config._replace(
                    cursor_position=self.topic_config.cursor_position
                    + max_records
                )
                if self.topic_config.raw_records:
                    return [
                        message
                        for (_, message) in self.topic_config.messages[
                            start:end
                        ]
                    ]
                else:
                    return [
                        message.value
                        for (_, message) in self.topic_config.messages[
                            start:end
                        ]
                    ]
            else:
                return []

    @topic_retry_decorator
    def between(self, start, end, timeout_ms=1500):
        def poll_next_record():
            raw_records = self._consumer.poll(
                timeout_ms=timeout_ms, max_records=1
            )
            record_in_list = [
                record
                for records in raw_records.values()
                for record in records
            ]
            if record_in_list:
                return record_in_list[0]
            else:
                return None

        if is_in_test_mode(self.topic_config):
            messages = [
                msg
                for t, msg in self.topic_config.messages
                if start <= t < end
            ]
            if not self.topic_config.raw_records:
                return [message.value for message in messages]
            else:
                return messages
        else:
            with temporary_rollback(self._consumer, start):
                start_timestamp = start.timestamp() * 1000
                end_timestamp = end.timestamp() * 1000

                messages = []
                record = poll_next_record()
                if record:
                    while start_timestamp <= record.timestamp < end_timestamp:
                        messages.append((record.timestamp, record))
                        record = poll_next_record()
                        if not record:
                            break

            if self.topic_config.raw_records:
                return [v for t, v in messages]
            else:
                return [v.value for t, v in messages]

    def close(self):
        if not is_in_test_mode(self.topic_config):
            self._consumer.close(autocommit=False)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next(timeout_ms=float("inf"))


class Producer:
    def __init__(self, topic_config):
        self.topic_config = topic_config
        if not is_in_test_mode(topic_config):
            self._producer = KafkaProducer(
                value_serializer=kirby_value_serializer,
                **get_kafka_args(topic_config),
            )

    @staticmethod
    def format_headers(headers):
        if isinstance(headers, dict):
            return [
                (k, kirby_value_serializer(v))
                for k, v in list(headers.items())
            ]
        else:
            raise RuntimeError(
                f"The format of given headers ({headers}) is not correct "
                "it must be a dictionary"
            )

    def send(self, message, submitted=None, headers=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        if headers is None:
            headers = {}

        if not is_in_test_mode(self.topic_config):
            timestamp_ms = int(submitted.timestamp() * 1000)
            topic_retry_decorator(self._producer.send)(
                self.topic_config.name,
                value=message,
                timestamp_ms=timestamp_ms,
                headers=self.format_headers(headers),
            )
            self._producer.flush()
        else:
            self.topic_config.messages.append(
                (
                    submitted,
                    ConsumerRecord(
                        topic=self.topic_config.name,
                        partition=0,
                        offset=len(self.topic_config.messages),
                        timestamp=submitted,
                        timestamp_type=0,
                        key=None,
                        value=message,
                        headers=[(k, v) for k, v in headers.items()],
                        checksum=None,
                        serialized_key_size=None,
                        serialized_value_size=None,
                        serialized_header_size=None,
                    ),
                )
            )

    def close(self):
        if not is_in_test_mode(self.topic_config):
            self._producer.close()


class Topic:
    def __init__(
        self,
        topic_name,
        group_id=None,
        use_tls=True,
        testing=False,
        raw_records=False,
    ):
        self.name = topic_name
        self.testing = testing
        if testing:
            self.topic_config = TopicTestModeConfig(
                name=topic_name,
                cursor_position=0,
                raw_records=raw_records,
                messages=[],
            )
        else:
            self.topic_config = TopicConfig(
                name=topic_name,
                group_id=ctx.PACKAGE_NAME if not group_id else group_id,
                use_tls=use_tls,
                raw_records=raw_records,
            )

        self._consumer = Consumer(self.topic_config)

        mode = "testing" if self.testing else "live"
        logger.debug(f"starting topic {topic_name} in {mode} mode")

    def safely_set_attribute_if_does_not_exist(
        self, item, class_, *args, **kargs
    ):
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            object.__setattr__(self, item, class_(*args, **kargs))

    @property
    def _producer(self):
        self.safely_set_attribute_if_does_not_exist(
            "_hidden_producer", Producer, self.topic_config
        )
        return self._hidden_producer

    def __getattr__(self, item):
        consumer_methods = [
            k for k, v in Consumer.__dict__.items() if callable(v)
        ]
        producer_methods = [
            k for k, v in Producer.__dict__.items() if callable(v)
        ]

        if item in consumer_methods:
            return getattr(object.__getattribute__(self, "_consumer"), item)
        elif item in producer_methods:
            return getattr(object.__getattribute__(self, "_producer"), item)
        else:
            raise AttributeError(
                f"Neither Topic, Consumer nor Producer "
                f"has an attribute named {item}"
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if not self.testing:
            try:
                object.__getattribute__(self, "_hidden_producer").close()
            except AttributeError:
                pass
            self._consumer.close()
