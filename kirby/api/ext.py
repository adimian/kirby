import msgpack
from kafka import KafkaConsumer, KafkaProducer


class Topic:
    def __init__(
        self, kirby_app, topic_name_variable_name, security_protocol="SSL"
    ):
        self.topic_name = kirby_app.ctx[topic_name_variable_name]
        self._args = {
            "bootstrap_servers": kirby_app.ctx.KAFKA_URL,
            "client_id": kirby_app.ctx.PACKAGE_NAME,
        }

        if security_protocol:
            self._args.update(
                {
                    "ssl_cafile": kirby_app.ctx.SSL_CAFILE,
                    "ssl_certfile": kirby_app.ctx.SSL_CERTFILE,
                    "ssl_keyfile": kirby_app.ctx.SSL_KEYFILE,
                    "security_protocol": "SSL",
                }
            )

        self.consumer = KafkaConsumer(
            group_id=kirby_app.ctx.PACKAGE_NAME, **self._args
        )
        self._subscribe_to_topic(self.topic_name)

    @property
    def producer(self):
        if not hasattr(self, "_producer"):
            self._producer = KafkaProducer(**self._args)
        return self._producer

    def _subscribe_to_topic(self, topic_name):
        self.consumer.subscribe([topic_name])
        self.consumer.poll()
        # We poll here to allow the consumer to have a partition assigned

    def send(self, item):
        message = msgpack.packb(item)
        self.producer.send(self.topic_name, value=message)
        self.producer.flush()

    @staticmethod
    def message_to_item(raw_message):
        if raw_message:
            for nested_message in raw_message.values():
                for message in nested_message:
                    return msgpack.unpackb(message.value, raw=False)

    def next(self, timeout_ms=500):
        message = self.consumer.poll(max_records=1, timeout_ms=timeout_ms)
        self.consumer.commit()
        return Topic.message_to_item(message)

    def close(self):
        if hasattr(self, "_producer"):
            self._producer.close()
        self.consumer.close(autocommit=False)
