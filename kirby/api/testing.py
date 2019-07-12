import datetime
import msgpack
from contextlib import contextmanager
from smart_getenv import getenv

from kafka import KafkaProducer

from kirby.api.ext import topic_retry_decorator
from kirby.api.context import ctx


@contextmanager
def topic_sender():
    args = {
        "client_id": "topic_sender",
        "bootstrap_servers": ctx.KAFKA_BOOTSTRAP_SERVERS,
        "value_serializer": msgpack.dumps,
    }
    if getenv("KAFKA_USE_TLS", type=bool):
        args.update(
            {
                "security_protocol": "SSL",
                "ssl_cafile": ctx.KAFKA_SSL_CAFILE,
                "ssl_certfile": ctx.KAFKA_SSL_CERTFILE,
                "ssl_keyfile": ctx.KAFKA_SSL_KEYFILE,
            }
        )
    producer = KafkaProducer(**args)

    @topic_retry_decorator
    def send(topic_name, data, submitted=None):
        if submitted is None:
            submitted = datetime.datetime.utcnow()

        timestamp_ms = int(submitted.timestamp() * 1000)
        producer.send(topic_name, value=data, timestamp_ms=timestamp_ms)
        producer.flush()

    yield send
    producer.close()
