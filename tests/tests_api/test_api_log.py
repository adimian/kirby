import os
import pytest

from kirby.api.log import Logger, LOGGER_TOPIC_NAME


@pytest.fixture
def topic_for_logger(kirby_topic_factory):
    with kirby_topic_factory(LOGGER_TOPIC_NAME, raw_record=True) as topic:
        yield topic


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_it_create_log_and_log_correctly(topic_for_logger):
    message = "Error message"

    logger = Logger()
    logger.log(message)

    assert topic_for_logger.next(timeout_ms=500).value == message


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
@pytest.mark.parametrize(
    "method_name", ["critical", "error", "warning", "info", "debug"]
)
def test_it_log_with_different_levels(method_name, topic_for_logger):
    message_value = "Error message"

    logger = Logger()
    getattr(logger, method_name)(message_value)

    message = topic_for_logger.next(timeout_ms=500)
    assert message.value == message_value
    assert message.headers["level"] == method_name
