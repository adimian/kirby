import os
from unittest.mock import patch
import pytest

from kirby.api.ext import WebClient, RETRIES, WAIT_BETWEEN_RETRIES


class MockResult:
    def __init__(self, status_code, json):
        self.status_code = status_code
        self._json = json
        self.url = "http://false_url.just_to_mock"
        self.text = str(self._json)

    def json(self):
        return self._json


class MockSession:
    def __init__(self, get=None, post=None):
        if get:
            self._return_get = get
        else:
            self._return_get = {}

        if post:
            self._return_post = post
        else:
            self._return_post = {}

        self.data = {}

    def get(self, key, *args, **kargs):
        if self._return_get:
            return self._return_get.pop(0)
        elif self.data[key]:
            return MockResult(200, self.data[key])
        else:
            raise RuntimeError(
                "Your test is not good, you didn't give any data to return"
            )

    def post(self, key, *args, **kargs):
        if self._return_post:
            return self._return_post.pop(0)
        else:
            self.data[key] = kargs["data"]


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

    session_mock.return_value = MockSession()
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
def test_kirby_ext_web_client_handle_empty_response(session_mock):
    data = {"foo": True}

    good_get = MockResult(status_code=200, json=data)

    mocking_effects = [
        MockResult(status_code=i, json={}) for i in [502, 504, 500, 501]
    ]  # Errors
    mocking_effects.append(
        MockResult(status_code=200, json={})
    )  # Empty answer

    for mocking_effect in mocking_effects:

        session_mock.return_value = MockSession(get=[mocking_effect, good_get])

        with WebClient(
            "external_server", "http://some.external.server"
        ) as web_client:
            web_client.post("orders", data)
            result = web_client.get("orders")
            assert result == data
