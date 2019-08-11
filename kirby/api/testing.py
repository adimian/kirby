from contextlib import contextmanager
from smart_getenv import getenv

from .ext.topic import topic_retry_decorator, TopicConfig, Producer


@contextmanager
def topic_sender():
    use_tls = getenv("KAFKA_USE_TLS", type=bool, default=False)
    topic_config = TopicConfig(
        name=None, group_id=None, use_tls=use_tls, raw_records=True
    )
    producer = Producer(topic_config)

    @topic_retry_decorator
    def send(topic_name, data, **kargs):
        Producer(topic_config._replace(name=topic_name)).send(
            data, **kargs
        )

    yield send
    producer.close()
