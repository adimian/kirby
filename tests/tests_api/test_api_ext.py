from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies, settings

from kafka.structs import TopicPartition
from kafka.consumer.fetcher import ConsumerRecord

from kirby.api.ext import WebClient, Topic, kirby_value_serializer


def test_creation_of_a_kirby_topic(kirby_topic_factory):
    with kirby_topic_factory("TOPIC_NAME", testing=True) as kirby_topic:
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


@strategies.composite
def record_by_partition(draw):
    data_strategies = strategies.builds(
        kirby_value_serializer,
        strategies.one_of(strategies.text(), strategies.none()),
    )

    return draw(
        strategies.fixed_dictionaries(
            {
                strategies.builds(
                    TopicPartition,
                    topic=strategies.text(),
                    partition=strategies.integers(),
                ): strategies.lists(
                    strategies.builds(
                        ConsumerRecord,
                        topic=strategies.text(),
                        partition=strategies.integers(),
                        offset=strategies.integers(),
                        timestamp=strategies.integers(),
                        timestamp_type=strategies.integers(),
                        key=strategies.none(),
                        value=data_strategies,
                        headers=strategies.lists(
                            strategies.tuples(
                                strategies.text(), data_strategies
                            )
                        ),
                        checksum=strategies.none(),
                        serialized_key_size=strategies.integers(),
                        serialized_value_size=strategies.integers(),
                        serialized_header_size=strategies.integers(),
                    )
                )
            }
        )
    )


@settings(deadline=500)
@given(record_by_partition())
def test_topic_can_parse_any_records(
    kirby_topic_factory, records_by_partition
):
    with kirby_topic_factory(
        "test", testing=True, raw_records=True
    ) as kirby_topic:
        kirby_topic.parse_records(records_by_partition=records_by_partition)


def test_topic_parse_corectly_records(kirby_topic_factory):
    headers = [
        ("header_1", u"välûe%_1ù"),
        ("header_2", u"välûe%_°2ù"),
        ("header_3", u"välûe%_$*3ù"),
    ]

    records_by_partition = {
        TopicPartition(topic="topic", partition="partition"): [
            ConsumerRecord(
                topic="topic",
                partition="partition",
                offset=0,
                timestamp=1562566,
                timestamp_type=0,
                key=None,
                value=kirby_value_serializer("value"),
                headers=[
                    (header[0], kirby_value_serializer(header[1]))
                    for header in headers
                ],
                checksum=None,
                serialized_key_size=None,
                serialized_value_size=None,
                serialized_header_size=None,
            )
        ]
    }

    with kirby_topic_factory(
        "test", testing=True, raw_records=True
    ) as kirby_topic:
        parsed_records = kirby_topic.parse_records(
            records_by_partition=records_by_partition
        )
        assert parsed_records[0].headers == {
            header[0]: header[1] for header in headers
        }
