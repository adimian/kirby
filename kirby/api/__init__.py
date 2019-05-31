import requests
import json
import logging
from pprint import pformat

import msgpack
from kafka import KafkaConsumer
from smart_getenv import getenv

from .context import ContextManager, ctx

logger = logging.getLogger(__name__)


class ServerError(BaseException):
    pass


class ClientError(BaseException):
    pass


class Kirby:
    def __init__(self, env_signature, session=None):
        ContextManager(env_signature)
        self.ctx = ctx
        self._session = session or requests.session()

        self._register()

    def get_topic_id(self, topic_name):
        result = self._session.get(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "topic"]),
            params={"name": topic_name},
        )
        if result.status_code != 200:
            if result.status_code == 500:
                raise ServerError("There is an issue with the web server.")
            else:
                raise ClientError(
                    f"There is no id from the name {topic_name}. "
                    f"Verify that the topic has been registered."
                )
        return result.json()["id"]

    def _register(self, source_id=None, destination_id=None):
        result = self._session.patch(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "registration"]),
            params={
                "script_id": self.ctx.ID,
                "source_id": source_id,
                "destination_id": destination_id,
            },
        )

        if result.status_code != 200:
            if result.status_code == 500:
                raise ServerError("There is an issue with the web server.")
            else:
                raise ClientError("There is an error with the id(s) given.")

    def add_source(self, source):
        self._register(source_id=self.get_topic_id(source.topic_name))

    def add_destination(self, destination):
        self._register(
            destination_id=self.get_topic_id(destination.topic_name)
        )


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
