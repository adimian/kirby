from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies

from kirby.api.ext import WebClient, Topic


def test_creation_of_a_kirby_topic(kirby_topic_factory):
    with kirby_topic_factory("TOPIC_NAME") as kirby_topic:
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


@strategies.composite
def wrong_headers(draw):
    data_strategies = strategies.one_of(
        strategies.text(), strategies.integers(), strategies.none()
    )
    return draw(
        strategies.recursive(
            data_strategies,
            lambda data: strategies.one_of(
                strategies.iterables(data), strategies.lists(data)
            ),
        )
    )


@pytest.mark.parametrize(
    "headers_to_format,expected_result",
    [
        ({}, []),
        ({"hello": "world"}, [("hello", b"\xa5world")]),
        ({"test": ["why", "not"]}, [("test", b"\x92\xa3why\xa3not")]),
    ],
)
def test_it_format_headers_correctly(headers_to_format, expected_result):
    assert Topic.format_headers(headers_to_format) == expected_result


@given(wrong_headers())
def test_it_raise_error_while_format_headers_error(headers):
    with pytest.raises(RuntimeError):
        Topic.format_headers(headers)
