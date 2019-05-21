from kirby.supervisor.consensus import Consensus


def test_it_can_elect_a_leader(monkeypatch, redis_test_key):
    monkeypatch.setenv("REDIS_LEADER_TTL", "1")
    monkeypatch.setenv(
        "REDIS_LEADER_KEY", f"{redis_test_key}test_it_can_elect_al_leader"
    )

    consensus_one = Consensus()
    consensus_two = Consensus()

    # The leader will be the first one to set its value
    assert consensus_one.is_leader()
    assert not consensus_two.is_leader()

    for _ in range(0, 10):
        assert consensus_one.is_leader()
        assert not consensus_two.is_leader()
