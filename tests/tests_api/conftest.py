import os

from contextlib import contextmanager
from pytest import fixture
from freezegun import freeze_time

from kirby.api import Kirby
from tests.conftest import API_ROOT
from kirby.api.ext.topic import Topic


DATE = "2019-05-22 15:18"
TOPIC_NAME = "orders"


@fixture
def kirby_hidden_env(db_scripts_not_registered):
    env = {
        # These are the "hidden" variables.
        "ID": "1",
        "PACKAGE_NAME": "orders_retriever",
        "KIRBY_WEB_SERVER": API_ROOT,
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


@fixture
@freeze_time(DATE)
def kirby_app(session, kirby_hidden_env, kirby_expected_env):
    return Kirby(kirby_expected_env, session=session)


@fixture
def kirby_topic_factory(kafka_topic_factory, is_in_test_mode, kafka_use_tls):
    import logging

    logger = logging.getLogger(__name__)

    @contextmanager
    def create_kirby_topic(topic_name, *args, timeout_ms=1500, **kargs):
        if not is_in_test_mode:
            kargs.update(use_tls=kafka_use_tls)
            with kafka_topic_factory(topic_name, timeout_ms=timeout_ms):
                with Topic(topic_name, *args, **kargs) as kirby_topic:
                    yield kirby_topic
        else:
            logger.warning(
                f"The Topic '{topic_name}' is created in testing mode"
            )
            kargs.update(testing=True)
            with Topic(topic_name, *args, **kargs) as kirby_topic:
                yield kirby_topic

    yield create_kirby_topic
