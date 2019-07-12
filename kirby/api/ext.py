import datetime
import logging
import msgpack
import requests
import tenacity
from functools import partial
from smart_getenv import getenv
from urllib.parse import urljoin

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable, NodeNotReadyError
from kafka.consumer.fetcher import ConsumerRecord

from .context import ctx

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


class WebClientError(Exception):
    pass


webserver_retry_decorator = tenacity.retry(
    retry=tenacity.retry_if_exception_type(WebClientError),
    wait=tenacity.wait_fixed(WAIT_BETWEEN_RETRIES),
    stop=tenacity.stop_after_attempt(RETRIES),
    reraise=True,
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


class Consumer:
    def __init__(self, topic):
        self.topic = topic
        if not self.topic.testing:
            self._consumer = KafkaConsumer(
                self.topic.name,
                group_id=self.topic.group_id,
                value_deserializer=kirby_value_deserializer,
                **topic.get_kafka_args(),
            )
            self._consumer.poll()

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
        if not self.topic.testing:
            return parse_records(
                self._get_nexts_kafka_records(timeout_ms, max_records),
                raw_records=self.topic.raw_records,
            )
        else:
            if self.topic._messages:
                start = self.topic.cursor_position
                end = self.topic.cursor_position + max_records
                self.topic.cursor_position += max_records
                if self.topic.raw_records:
                    return [
                        message
                        for (_, message) in self.topic._messages[start:end]
                    ]
                else:
                    return [
                        message.value
                        for (_, message) in self.topic._messages[start:end]
                    ]
            else:
                return None

    @topic_retry_decorator
    def between(self, start, end):
        if self.topic.testing:
            messages = [
                msg for t, msg in self.topic._messages if start <= t < end
            ]
            if messages:
                self.topic.cursor_position = [
                    msg for t, msg in self.topic._messages
                ].index(messages[-1])
            if not self.topic.raw_records:
                return [message.value for message in messages]
            else:
                return messages
        else:
            partitions = self._consumer.assignment()

            start_mapping = {p: start.timestamp() for p in partitions}
            start_offsets = self._consumer.offsets_for_times(start_mapping)

            start_timestamp = start.timestamp() * 1000
            end_timestamp = end.timestamp() * 1000

            # with modify_temporarily_offsets(self._consumer, partitions):
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

    def close(self):
        if not self.topic.testing:
            self._consumer.close(autocommit=False)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next(timeout_ms=float("inf"))


class Producer:
    def __init__(self, topic):
        self.topic = topic
        if not self.topic.testing:
            self._producer = KafkaProducer(
                value_serializer=kirby_value_serializer,
                **topic.get_kafka_args(),
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

        if not self.topic.testing:
            timestamp_ms = int(submitted.timestamp() * 1000)
            topic_retry_decorator(self._producer.send)(
                self.topic.name,
                value=message,
                timestamp_ms=timestamp_ms,
                headers=self.format_headers(headers),
            )
            self._producer.flush()
        else:
            self.topic._messages.append(
                (
                    submitted,
                    ConsumerRecord(
                        topic=self.topic.name,
                        partition=0,
                        offset=len(self.topic._messages),
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
        if not self.topic.testing:
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
        self.use_tls = use_tls
        self.raw_records = raw_records

        if self.testing:
            self.group_id = group_id
            self._messages = []
            self.cursor_position = 0
        else:
            self.group_id = ctx.PACKAGE_NAME if not group_id else group_id

        mode = "testing" if self.testing else "live"
        logger.debug(f"starting topic {self.name} in {mode} mode")

    def safely_set_attribute_if_does_not_exist(
        self, item, class_, *args, **kargs
    ):
        try:
            object.__getattribute__(self, item)
        except AttributeError:
            object.__setattr__(self, item, class_(*args, **kargs))

    def get_kafka_args(self):
        if not self.testing:
            kafka_args = {"bootstrap_servers": ctx.KAFKA_BOOTSTRAP_SERVERS}
            if self.use_tls:
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

    @property
    def _producer(self):
        args = [self]
        self.safely_set_attribute_if_does_not_exist(
            "_hidden_producer", Producer, *args
        )
        return self._hidden_producer

    @property
    def _consumer(self):
        args = [self]
        self.safely_set_attribute_if_does_not_exist(
            "_hidden_consumer", Consumer, *args
        )
        return self._hidden_consumer

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
        if not self.testing:
            try:
                object.__getattribute__(self, "_hidden_producer").close()
            except AttributeError:
                pass
            try:
                object.__getattribute__(self, "_hidden_consumer").close()
            except AttributeError:
                pass


class WebClient:
    def __init__(self, name, web_endpoint_base, session=None):
        self.name = name
        self.web_endpoint_base = web_endpoint_base
        self._session = session or requests.session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _request_decorator(self, method):
        def request(endpoint, **kwargs):
            result = method(
                urljoin(self.web_endpoint_base, endpoint), **kwargs
            )

            if result.status_code == 200:
                return result.json()
            raise WebClientError(
                f"{method} error on {result.url}. "
                f"Status code : {result.status_code}. "
                f"Response : {result.text}"
            )

        return webserver_retry_decorator(request)

    def __getattr__(self, item):
        method = getattr(self._session, item)
        if callable(method):
            return self._request_decorator(method)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            )
