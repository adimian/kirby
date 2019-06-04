import logging
import datetime
import msgpack
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

logger = logging.getLogger(__name__)


def retry(function):

    NB_RETRY = 3

    def function_decorated():
        for counter in range(NB_RETRY):
            try:
                return_value = function_decorated()
            except NoBrokersAvailable as e:
                if counter == NB_RETRY:
                    logger.error(
                        f"The function {function.__name__} was "
                        f"launched {counter + 1} times without success."
                    )
                    raise e
            else:
                logger.info(
                    f"The function {function.__name__} was "
                    f"launched {counter + 1} times and succeed."
                )
                return return_value

    return function


class Topic:
    def __init__(
        self,
        kirby_app,
        topic_name_variable_name,
        security_protocol="SSL",
        testing=False,
    ):
        self.name = kirby_app.ctx[topic_name_variable_name]
        self.testing = testing
        mode = "testing" if self.testing else "live"
        logger.debug(f"starting topic {self.name} in {mode} mode")
        self.init_kafka(kirby_app, security_protocol)

    @retry
    def init_kafka(self, kirby_app, security_protocol):
        self._args = {
            "bootstrap_servers": kirby_app.ctx.KAFKA_BOOTSTRAP_SERVERS
        }

        if security_protocol:
            self._args.update(
                {
                    "ssl_cafile": kirby_app.ctx.KAFKA_SSL_CAFILE,
                    "ssl_certfile": kirby_app.ctx.KAFKA_SSL_CERTFILE,
                    "ssl_keyfile": kirby_app.ctx.KAFKA_SSL_KEYFILE,
                    "security_protocol": "SSL",
                }
            )
        if self.testing:
            self._messages = []
            self.cursor_position = 0
        else:
            self._consumer = KafkaConsumer(
                self.name,
                group_id=kirby_app.ctx.PACKAGE_NAME,
                value_deserializer=lambda x: msgpack.loads(x, raw=False),
                **self._args,
            )
            self._producer = KafkaProducer(
                value_serializer=msgpack.dumps, **self._args
            )

    @retry
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

    @staticmethod
    def message_to_item(raw_message):
        if raw_message:
            for messages_by_topic in raw_message.values():
                for message in messages_by_topic:
                    return message.value

    @retry
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
