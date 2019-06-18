from unittest.mock import patch, MagicMock
import pytest

from kirby.api.ext import WebClient


def test_creation_of_a_kirby_topic(kirby_topic):
    assert not kirby_topic.next()

    kirby_topic.send("Hello world")

    assert kirby_topic.next() == "Hello world"


@patch("requests.session")
def test_creation_of_a_web_client(session_mock):
    data = {"foo": True}

    session_mock.return_value.get.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value=data)
    )

    session_mock.return_value.post.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )
    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        web_client.post("orders", data)
        assert web_client.get("orders") == data


@pytest.mark.parametrize("bad_return_value", [502, 504, 500, 501, 200])
@patch("requests.session")
def test_web_client_handle_get_errors(session_mock, bad_return_value):
    data = {"foo": True}
    session_mock.return_value.post.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )
    session_mock.return_value.get.side_effect = [
        MagicMock(
            status_code=bad_return_value, json=MagicMock(return_value={})
        ),
        MagicMock(status_code=200, json=MagicMock(return_value=data)),
    ]

    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        web_client.post("orders", data)
        result = web_client.get("orders")
        assert result == data


@patch("requests.session")
def test_web_client_handle_post_errors(session_mock):
    data = {"foo": True}
    session_mock.return_value.get.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value=data)
    )
    session_mock.return_value.post.side_effect = [
        MagicMock(status_code=500, json=MagicMock(return_value={})),
        MagicMock(status_code=200, json=MagicMock(return_value={})),
    ]
    with WebClient(
        "external_server", "http://some.external.server"
    ) as web_client:
        web_client.post("orders", data)
        result = web_client.get("orders")
        assert result == data
