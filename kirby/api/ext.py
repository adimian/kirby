import logging
import datetime
import requests
import msgpack
from smart_getenv import getenv
import tenacity

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

logger = logging.getLogger(__name__)

RETRIES = getenv("EXT_RETRIES", type=int)
WAIT_BETWEEN_RETRIES = getenv("EXT_WAIT_BETWEEN_RETRIES", type=float)
kafka_retry_args = {
    "retry": tenacity.retry_if_exception_type(NoBrokersAvailable),
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


class Topic:
    def __init__(
        self,
        kirby_app,
        topic_name_variable_name,
        ssl_security_protocol=True,
        testing=False,
    ):
        self.name = kirby_app.ctx[topic_name_variable_name]
        self.testing = testing
        self.ssl_security_protocol = ssl_security_protocol
        self.kirby_app = kirby_app
        self.init_kafka()
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting topic {self.name} in {mode} mode")

    @tenacity.retry(**kafka_retry_args)
    def init_kafka(self):
        kafka_args = {
            "bootstrap_servers": self.kirby_app.ctx.KAFKA_BOOTSTRAP_SERVERS
        }

        if self.ssl_security_protocol:
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
                value_deserializer=lambda x: msgpack.loads(x, raw=False),
                **kafka_args,
            )
            self._producer = KafkaProducer(
                value_serializer=msgpack.dumps, **kafka_args
            )

    @tenacity.retry(**kafka_retry_args)
    def send(self, message, submitted=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        if self.testing:
            self._messages.append((submitted, message))

        else:
            timestamp_ms = int(submitted.timestamp() * 1000)
            self._producer.send(
                self.name, value=message, timestamp_ms=timestamp_ms
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

    @staticmethod
    def message_to_item(raw_message):
        if raw_message:
            for messages_by_topic in raw_message.values():
                for message in messages_by_topic:
                    return message.value

    @tenacity.retry(**kafka_retry_args)
    def next(self, timeout_ms=500):
        if not self.testing:
            message = self._consumer.poll(max_records=1, timeout_ms=timeout_ms)
            self._consumer.commit()
            return self.message_to_item(message)
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


class WebClient:
    def __init__(self, name, web_endpoint_base, session=None):
        self.name = name
        self.web_endpoint_base = web_endpoint_base
        self._session = session or requests.session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @tenacity.retry(**webserver_retry_args)
    def post(self, endpoint, data, params=None):
        if not params:
            params = {}
        result = self._session.post(
            "/".join([self.web_endpoint_base, endpoint]),
            data=data,
            params=params,
        )
        if result.status_code == 200:
            return result.json()
        raise WebClientError(
            f"POST error on {result.url}. "
            f"Status code : {result.status_code}. "
            f"Response : {result.text}"
        )

    @tenacity.retry(**webserver_retry_args)
    def get(self, endpoint, params=None):
        result = self._session.get(
            "/".join([self.web_endpoint_base, endpoint]), params=params
        )
        if result.status_code == 200:
            json = result.json()
            if json:
                return json
        raise WebClientError(
            f"GET error on {result.url}. "
            f"Status code : {result.status_code}. "
            f"Response : {result.text}"
        )
