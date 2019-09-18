from contextlib import contextmanager
from smart_getenv import getenv

from .ext.topic import topic_retry_decorator, TopicConfig, Producer


@contextmanager
def topic_sender():
    use_tls = getenv("KAFKA_USE_TLS", type=bool, default=False)
    topic_config = TopicConfig(
        name=None, group_id=None, use_tls=use_tls, raw_records=True
    )
    producers = {}

    @topic_retry_decorator
    def send(topic_name, data, **kargs):
        if topic_name not in producers.keys():
            producers[topic_name] = Producer(
                topic_config._replace(name=topic_name)
            )
        producers[topic_name].send(data, **kargs)

    yield send

    for p in producers.values():
        p.close()
