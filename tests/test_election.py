import pytest
from kirby.supervisor.election import Election, make_me_leader
from redis import Redis


@pytest.fixture
def redis():
    redis = Redis()
    redis.flushall()
    yield redis


def test_it_can_make_leader(redis):
    assert make_me_leader("server-1", redis, 0.1)


def test_it_can_elect_a_leader_with_a_single_node(redis):
    with Election("server-1", server=redis, check_ttl=0.1) as bob:
        assert bob.is_leader()


def test_it_can_elect_a_leader_but_not_two(redis):
    with Election("alice", server=redis, check_ttl=0.1) as alice:
        with Election("bob", server=redis, check_ttl=0.1) as bob:
            assert alice.is_leader() ^ bob.is_leader()


def test_it_can_elect_a_new_leader_when_second_stops(redis):
    with Election("alice", server=redis, check_ttl=0.1) as alice:
        assert alice.is_leader()

    redis.flushall()
    with Election("bob", server=redis, check_ttl=0.1) as bob:
        assert bob.is_leader()
