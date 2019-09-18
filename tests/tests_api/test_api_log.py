import os
from smart_getenv import getenv
import pytest
from hypothesis import given, strategies, settings

from kirby.api.log import Logger, LogReader, LOGGER_TOPIC_NAME


@pytest.fixture
def topic_for_logger(kirby_topic_factory):
    with kirby_topic_factory(LOGGER_TOPIC_NAME, raw_records=True) as topic:
        yield topic


@pytest.fixture
def logger():
    logger = Logger(
        default_level="error",
        use_tls=getenv("KAFKA_USE_TLS", type=bool, default=True),
    )
    return logger


@pytest.fixture
def log_reader():
    yield LogReader(use_tls=getenv("KAFKA_USE_TLS", type=bool, default=True))


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_it_create_log_and_log_correctly(topic_for_logger, logger):
    message = "Error message"
    logger.log(message)

    assert topic_for_logger.next().value == message


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
@pytest.mark.parametrize(
    "method_name", ["critical", "error", "warning", "info", "debug"]
)
def test_it_log_with_different_levels(method_name, topic_for_logger, logger):
    message_value = "Error message"
    getattr(logger, method_name)(message_value)

    message = topic_for_logger.next()
    assert message.value == message_value
    assert message.headers["level"] == method_name


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
@settings(deadline=6000, max_examples=3)
@given(strategies.text(min_size=10))
def test_it_create_a_log_reader(topic_for_logger, log_reader, message):
    topic_for_logger.send(message)
    assert log_reader.next().value == message


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_integration_logger_and_log_reader(
    kafka_topic_factory, logger, log_reader
):
    message = "Hello world"
    with kafka_topic_factory(LOGGER_TOPIC_NAME):
        logger.info(message)

        retrieved_message = log_reader.next()
        assert retrieved_message.value == message
        assert retrieved_message.headers["level"] == "info"
