import pytest
import os

from tests.tests_api.conftest import TOPIC_NAME

from kirby.api.testing import topic_sender


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_that_topic_sender_populate_a_topic(kirby_topic_factory):
    with kirby_topic_factory(TOPIC_NAME) as kirby_topic:
        data = "Hello world"
        with topic_sender() as send_function:
            send_function(TOPIC_NAME, data)

        assert kirby_topic.next() == data
