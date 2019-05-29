import json
import logging
from pprint import pformat

import msgpack
from kafka import KafkaConsumer
from smart_getenv import getenv

logger = logging.getLogger(__name__)


def read_topic(name):
    bootstrap_servers = getenv(
        "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
    )
    consumer = KafkaConsumer(
        name,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=msgpack.loads,
    )

    for idx, message in enumerate(consumer, start=1):
        message = message.value
        try:
            message = json.loads(message.decode("utf-8"))
            logger.debug(pformat(message))
        except Exception:
            logger.debug(message)
