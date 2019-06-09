import os
from smart_getenv import getenv
from pytest import fixture
from freezegun import freeze_time

from kirby.api import Kirby
from kirby.api.ext import Topic
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


@fixture(scope="function")
def kirby_topic(kirby_app, kafka_topic_factory):
    import logging

    logger = logging.getLogger(__name__)
    bootstrap_servers = getenv(
        "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
    )
    if bootstrap_servers:
        with kafka_topic_factory(TOPIC_NAME):
            with Topic(kirby_app, "TOPIC_NAME") as topic:
                yield topic
    else:
        logger.warning(
            f"There is no KAFKA_BOOTSTRAP_SERVERS. "
            f"Topic will be created in testing mode"
        )
        with Topic(kirby_app, "TOPIC_NAME", testing=True) as topic:
            yield topic
