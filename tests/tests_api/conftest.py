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

SSL_CAFILE = "ca.pem"
SSL_CERTFILE = "service.cert"
SSL_KEYFILE = "service.key"


@fixture
def kirby_hidden_env(db_scripts_not_registered):
    env = {
        # These are the "hidden" variables.
        "ID": "2",
        "PACKAGE_NAME": "cashregister_retriever",
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


class init_kafka_topic:
    def __init__(self, topic_name):
        self.topic_name = topic_name
        self.admin = KafkaAdminClient(
            bootstrap_servers=KAFKA_URL,
            client_id="Admin_test",
            ssl_cafile=SSL_CAFILE,
            ssl_certfile=SSL_CERTFILE,
            ssl_keyfile=SSL_KEYFILE,
            security_protocol="SSL",
        )

    def __enter__(self):
        return_value = self.admin.create_topics(
            [NewTopic(self.topic_name, 1, 1)]
        )
        # Assert that there where no errors during the creation of the topic
        assert return_value.topic_errors[0][1] == 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.admin.delete_topics([self.topic_name])
        self.admin.close()


@fixture(scope="function")
def kirby_topic(kirby_app):
    with init_kafka_topic(TOPIC_NAME) as topic_name:
        topic = Topic(kirby_app, "TOPIC_NAME")
        yield topic
    topic.close()
