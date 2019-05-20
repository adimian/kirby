import time


def test_it_can_connect_to_redis(redis_proxy):
    assert redis_proxy.client.ping()


def test_it_can_get_values(redis_proxy, redis_test_key):
    key = redis_test_key + "test_it_can_get_values"

    assert not redis_proxy.get(key)
    redis_proxy.client.set(key, "Test value")
    assert redis_proxy.get(key)


def test_it_decodes_response_from_get(redis_proxy, redis_test_key):
    key = redis_test_key + "test_it_decodes_response_from_get"
    redis_proxy.client.set(key, "Hello this will be encoded to bytes.")

    assert isinstance(redis_proxy.client.get(key), bytes)
    assert isinstance(redis_proxy.get(key), str)


def test_it_can_set_value_with_ttl(redis_proxy, redis_test_key):
    key = redis_test_key + "test_it_can_set_value_with_ttl"
    ttl = 1

    redis_proxy.set_value_with_ttl(key, "test", ttl)
    assert redis_proxy.get(key)

    time.sleep(ttl + 0.1)
    assert not redis_proxy.get(key)


def test_it_only_sets_value_if_key_was_not_set(redis_proxy, redis_test_key):
    key = redis_test_key + "test_it_cannot_set_value_if_key_was_set"
    first_value = "test_one"

    assert not redis_proxy.get(key)

    redis_proxy.set_value_with_ttl(key, first_value, 1)
    redis_proxy.set_value_with_ttl(key, "other random value", 1)

    assert redis_proxy.get(key) == first_value

    redis_proxy.set_value_with_ttl(key, "yet another random value", 1)

    assert redis_proxy.get(key) == first_value
