import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies

from kafka.structs import TopicPartition
from kafka.consumer.fetcher import ConsumerRecord

from kirby.api.ext.topic import Producer, kirby_value_serializer, parse_records


def test_creation_of_a_kirby_topic(kirby_topic_factory):
    with kirby_topic_factory("TOPIC_NAME") as kirby_topic:
        assert not kirby_topic.next()

        kirby_topic.send("Hello world")

        assert kirby_topic.next() == "Hello world"


@pytest.mark.parametrize(
    "headers_to_format,expected_result",
    [
        ({}, []),
        ({"hello": "world"}, [("hello", b"\xa5world")]),
        ({"test": ["why", "not"]}, [("test", b"\x92\xa3why\xa3not")]),
    ],
)
def test_it_format_headers_correctly(headers_to_format, expected_result):
    assert Producer.format_headers(headers_to_format) == expected_result


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


@given(wrong_headers())
def test_it_raise_error_while_format_headers_error(headers):
    with pytest.raises(RuntimeError):
        Producer.format_headers(headers)


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
                    ),
                    min_size=1,
                )
            }
        )
    )


@given(record_by_partition())
def test_topic_can_parse_any_records(records_by_partition):
    parse_records(records_by_partition)


def test_topic_parse_correctly_records():
    headers = [
        ("header_1", "välûe%_1ù"),
        ("header_2", "välûe%_°2ù"),
        ("header_3", "välûe%_$*3ù"),
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

    parsed_records = parse_records(records_by_partition, raw_records=True)
    assert parsed_records[0].headers == {
        header[0]: header[1] for header in headers
    }


def test_topic_can_rollback(kirby_topic_factory):
    now = datetime(year=2019, month=7, day=18, hour=15, minute=39)
    delta = timedelta(hours=1)

    with kirby_topic_factory("TOPIC_NAME", init_time=now) as kirby_topic:
        for i in range(10):
            kirby_topic.send(i, submitted=now + i * delta)

        assert kirby_topic.between(now + 4 * delta, now + 8 * delta) == [
            4,
            5,
            6,
            7,
        ]


def test_topic_rollback_is_temporary(kirby_topic_factory):
    now = datetime(year=2019, month=7, day=24, hour=10, minute=45)
    delta = timedelta(hours=1)

    with kirby_topic_factory("TOPIC_NAME", init_time=now) as kirby_topic:
        for i in range(10):
            kirby_topic.send(i, submitted=now + i * delta)

        assert kirby_topic.next() == 0

        kirby_topic.between(now + 4 * delta, now + 8 * delta)

        assert kirby_topic.next() == 1
