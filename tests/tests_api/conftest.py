import os
from smart_getenv import getenv
from contextlib import contextmanager
from pytest import fixture
from freezegun import freeze_time
import tenacity

from kirby.api import Kirby
from kirby.api.ext import Topic, kafka_retry_args
from tests.conftest import API_ROOT


DATE = "2019-05-22 15:18"
TOPIC_NAME = "orders"


@fixture
def kirby_hidden_env(db_scripts_not_registered):
    env = {
        # These are the "hidden" variables.
        "ID": "1",
        "PACKAGE_NAME": "orders_retriever",
        "KIRBY_WEB_SERVER": API_ROOT,
        # "KAFKA_BOOTSTRAP_SERVERS": KAFKA_BOOTSTRAP_SERVERS,
        # ---
        # These are the one defined into the signature when Kirby is called.
        # They are specifics to the script.
        "WEBCLIENT_ENDPOINT": "http://a.place.somewhere",
        "TOPIC_NAME": TOPIC_NAME,
    }

    for k, v in env.items():
        os.environ[k] = v
    return env


@fixture
def kirby_expected_env():
    return {"WEBCLIENT_ENDPOINT": {"type": str}, "TOPIC_NAME": {"type": str}}


@fixture(scope="function")
@freeze_time(DATE)
def kirby_app(session, kirby_hidden_env, kirby_expected_env):
    return Kirby(kirby_expected_env, session=session)


@fixture
def kirby_topic_factory(kirby_app, kafka_topic_factory):
    import logging

    logger = logging.getLogger(__name__)
    bootstrap_servers = getenv(
        "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
    )
    topics = []

    @tenacity.retry(**kafka_retry_args)
    @contextmanager
    def create_kirby_topic(topic_name, **kargs):
        if bootstrap_servers:
            with kafka_topic_factory(topic_name):
                topic = Topic(kirby_app, topic_name, **kargs)
                topics.append(topic)
                yield topic
        else:
            logger.warning(
                f"There is no KAFKA_BOOTSTRAP_SERVERS. "
                "Topic will be created in testing mode"
            )
            topic = Topic(kirby_app, topic_name, testing=True)
            topics.append(topic)
            yield topic

    yield create_kirby_topic

    for topic in topics:
        topic.close()
