import os
from unittest.mock import patch, MagicMock, call
import pytest

from tests.tests_api.conftest import TOPIC_NAME

from kirby.api.ext import WebClient, topic_sender


def test_creation_of_a_kirby_topic(kirby_topic):
    assert not kirby_topic.next()

    kirby_topic.send("Hello world")

    assert kirby_topic.next() == "Hello world"


@pytest.mark.parametrize(
    "method", ["get", "post", "put", "delete", "head", "options"]
)
@patch("requests.session")
def test_web_client_calls_requests_session_methods(session_mock, method):
    data = {"foo": True}

    method_mocked = MagicMock(
        return_value=MagicMock(
            status_code=200, json=MagicMock(return_value=data)
        )
    )

    session_mock.return_value = MagicMock(**{method: method_mocked})

    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        assert getattr(web_client, method)("an_endoint") == data
        method_mocked.assert_called_once_with(
            "http://some.external.server/an_endoint"
        )


@pytest.mark.parametrize("bad_return_value", [502, 504, 500, 501])
@pytest.mark.parametrize(
    "method", ["get", "post", "put", "delete", "head", "options"]
)
@patch("requests.session")
def test_web_client_handle_errors_of_connection(
    session_mock, method, bad_return_value
):
    data = {"foo": True}

    method_mocked = MagicMock(
        side_effect=[
            MagicMock(
                status_code=bad_return_value, json=MagicMock(return_value={})
            ),
            MagicMock(status_code=200, json=MagicMock(return_value=data)),
        ]
    )

    session_mock.return_value = MagicMock(**{method: method_mocked})

    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        assert getattr(web_client, method)("an_endoint") == data
        method_mocked.assert_called_with(
            "http://some.external.server/an_endoint"
        )


def test_web_client_cannot_access_session_attribute():
    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        with pytest.raises(AttributeError):
            assert web_client.headers


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_that_topic_sender_populate_a_topic(kirby_topic):
    data = "Hello world"

    assert not kirby_topic.next()

    with topic_sender() as send_function:
        send_function(TOPIC_NAME, data)

    assert kirby_topic.next() == data
