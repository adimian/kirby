import os
from pytest import fixture
from freezegun import freeze_time

from kafka import KafkaAdminClient
from kafka.admin import NewTopic

from kirby.api import Kirby
from kirby.api.ext import Topic
from tests.conftest import API_ROOT

DATE = "2019-05-22 15:18"
KAFKA_URL = ""
TOPIC_NAME = "orders"

DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)))
SSL_CAFILE = os.path.join(DIR_PATH, "ca.pem")
SSL_CERTFILE = os.path.join(DIR_PATH, "service.cert")
SSL_KEYFILE = os.path.join(DIR_PATH, "service.key")


@fixture
def kirby_hidden_env(db_scripts_not_registered):
    env = {
        # These are the "hidden" variables.
        "ID": "1",
        "PACKAGE_NAME": "orders_retriever",
        "KIRBY_WEB_SERVER": API_ROOT,
        "KAFKA_URL": KAFKA_URL,
        "SSL_CAFILE": SSL_CAFILE,
        "SSL_CERTFILE": SSL_CERTFILE,
        "SSL_KEYFILE": SSL_KEYFILE,
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
def kirby_topic_factory(kirby_app):

    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_URL,
        client_id="Admin_test",
        ssl_cafile=SSL_CAFILE,
        ssl_certfile=SSL_CERTFILE,
        ssl_keyfile=SSL_KEYFILE,
        security_protocol="SSL",
    )
    created_topics = []

    def create_kirby_topic(topic_name):
        os.environ["TOPIC_NAME"] = topic_name
        return_value = admin.create_topics(
            [NewTopic(topic_name, 1, 1)], timeout_ms=1500
        )
        assert return_value.topic_errors[0][1] == 0

        topic = Topic(kirby_app, "TOPIC_NAME")
        created_topics.append(topic_name)
        return topic

    yield create_kirby_topic

    admin.delete_topics(created_topics)
    admin.close()
