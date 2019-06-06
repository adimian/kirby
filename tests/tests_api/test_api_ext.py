from unittest.mock import patch, MagicMock
import pytest

from kirby.api.ext import WebClient, RETRIES, WAIT_BETWEEN_RETRIES


def test_it_creates_a_kirby_topic(kirby_topic):
    assert not kirby_topic.next()

    kirby_topic.send("Hello world")

    assert kirby_topic.next() == "Hello world"


@pytest.mark.integration
@pytest.mark.skipif(
    not (RETRIES and WAIT_BETWEEN_RETRIES),
    reason="missing EXT_RETRIES and/or WAIT_BETWEEN_RETRIES environment variable",
)
@patch("requests.session")
def test_it_creates_a_kirby_ext_web_client(session_mock):
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


@pytest.mark.integration
@pytest.mark.skipif(
    not (RETRIES and WAIT_BETWEEN_RETRIES),
    reason="missing EXT_RETRIES and/or WAIT_BETWEEN_RETRIES environment variable",
)
@patch("requests.session")
def test_kirby_ext_web_client_handle_get_errors(session_mock):
    data = {"foo": True}

    good_get = MagicMock(status_code=200, json=MagicMock(return_value=data))

    mocking_effects = [
        MagicMock(status_code=i, json=MagicMock(return_value={}))
        for i in [502, 504, 500, 501]
    ]  # Errors
    mocking_effects.append(
        MagicMock(status_code=200, json=MagicMock(return_value={}))
    )  # Empty answer

    session_mock.return_value.post.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )
    for mocking_effect in mocking_effects:
        session_mock.return_value.get.side_effect = [mocking_effect, good_get]

        with WebClient(
            "external_server", "http://some.external.server"
        ) as web_client:
            web_client.post("orders", data)
            result = web_client.get("orders")
            assert result == data


@pytest.mark.integration
@pytest.mark.skipif(
    not (RETRIES and WAIT_BETWEEN_RETRIES),
    reason="missing EXT_RETRIES and/or WAIT_BETWEEN_RETRIES environment variable",
)
@patch("requests.session")
def test_kirby_ext_web_client_handle_post_errors(session_mock):
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
