import datetime
import logging
from functools import partial
from urllib.parse import urljoin
import msgpack
import requests
import tenacity
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable, NodeNotReadyError
from smart_getenv import getenv

logger = logging.getLogger(__name__)

RETRIES = getenv("EXT_RETRIES", type=int, default=3)
WAIT_BETWEEN_RETRIES = getenv(
    "EXT_WAIT_BETWEEN_RETRIES", type=float, default=0.4
)
kafka_retry_args = {
    "retry": (
        tenacity.retry_if_exception_type(NoBrokersAvailable)
        | tenacity.retry_if_exception_type(NodeNotReadyError)
    ),
    "wait": tenacity.wait_fixed(WAIT_BETWEEN_RETRIES),
    "stop": tenacity.stop_after_attempt(RETRIES),
    "reraise": True,
}


class WebClientError(Exception):
    pass


webserver_retry_args = {
    "retry": tenacity.retry_if_exception_type(WebClientError),
    "wait": tenacity.wait_fixed(WAIT_BETWEEN_RETRIES),
    "stop": tenacity.stop_after_attempt(RETRIES),
    "reraise": True,
}


kirby_value_deserializer = partial(msgpack.loads, raw=False)
kirby_value_serializer = msgpack.dumps


class Topic:
    def __init__(
        self,
        kirby_app,
        topic_name,
        use_tls=True,
        raw_record=False,
        testing=False,
    ):
        self.name = topic_name
        self.testing = testing
        self.use_tls = use_tls
        self.raw_record = raw_record
        self.kirby_app = kirby_app
        self.init_kafka()
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting topic {self.name} in {mode} mode")

    @tenacity.retry(**kafka_retry_args)
    def init_kafka(self):
        kafka_args = {
            "bootstrap_servers": self.kirby_app.ctx.KAFKA_BOOTSTRAP_SERVERS
        }

        if self.use_tls:
            kafka_args.update(
                {
                    "ssl_cafile": self.kirby_app.ctx.KAFKA_SSL_CAFILE,
                    "ssl_certfile": self.kirby_app.ctx.KAFKA_SSL_CERTFILE,
                    "ssl_keyfile": self.kirby_app.ctx.KAFKA_SSL_KEYFILE,
                    "security_protocol": "SSL",
                }
            )
        if self.testing:
            self._messages = []
            self.cursor_position = 0
        else:
            self._consumer = KafkaConsumer(
                self.name,
                group_id=self.kirby_app.ctx.PACKAGE_NAME,
                value_deserializer=kirby_value_deserializer,
                **kafka_args,
            )
            self._consumer.poll()
            self._producer = KafkaProducer(
                value_serializer=kirby_value_serializer, **kafka_args
            )

    @staticmethod
    def format_headers(headers):
        if isinstance(headers, dict):
            return [
                (header[0], kirby_value_serializer(header[1]))
                for header in list(headers.items())
            ]
        else:
            raise RuntimeError(
                f"The format of given headers ({headers}) is not correct "
                "it must be a dictionary"
            )

    @tenacity.retry(**kafka_retry_args)
    def send(self, message, submitted=None, headers=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        if headers is None:
            headers = {}

        if self.testing:
            self._messages.append((submitted, message))

        else:
            timestamp_ms = int(submitted.timestamp() * 1000)
            self._producer.send(
                self.name,
                value=message,
                timestamp_ms=timestamp_ms,
                headers=self.format_headers(headers),
            )
            self._producer.flush()

    @tenacity.retry(**kafka_retry_args)
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

    def parse_records(self, records_by_partition):
        if records_by_partition:
            if self.raw_record:
                records_to_return = []
                for records in records_by_partition.values():
                    for record in records:
                        headers_deserialized = {
                            k: kirby_value_deserializer(v)
                            for k, v in record.headers
                        }
                        records_to_return.append(
                            record._replace(headers=headers_deserialized)
                        )
                return records_to_return
            else:
                return [
                    record.value
                    for records in records_by_partition.values()
                    for record in records
                ]

    @tenacity.retry(**kafka_retry_args)
    def next(self, timeout_ms=500, max_records=1):
        if not self.testing:
            message = self._consumer.poll(
                max_records=max_records, timeout_ms=timeout_ms
            )
            self._consumer.commit()
            if message:
                parsed_messages = self.parse_records(message)
                if max_records == 1:
                    return parsed_messages[0]
                else:
                    return parsed_messages
            else:
                return None
        else:
            if self._messages:
                (_, message) = self._messages[self.cursor_position]
                self.cursor_position += 1
                return message
            else:
                return None

    def close(self):
        if not self.testing:
            self._producer.close()
            self._consumer.close(autocommit=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next(timeout_ms=float("inf"))


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

        return tenacity.retry(**webserver_retry_args)(request)

    def __getattr__(self, item):
        method = getattr(self._session, item)
        if callable(method):
            return self._request_decorator(method)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            )
