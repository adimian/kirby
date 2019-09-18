from unittest.mock import patch, MagicMock
import pytest

from kirby.api.ext.webclient import WebClient


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
