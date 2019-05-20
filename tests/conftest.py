import pytest

from kirby.proxy.redis_proxy import RedisProxy


REDIS_TEST_KEY = "kirby_test_"


@pytest.fixture
def redis_test_key():
    return REDIS_TEST_KEY


@pytest.fixture
def redis_proxy():
    proxy = RedisProxy()
    yield proxy
    for key in proxy.client.keys(f"{REDIS_TEST_KEY}*"):
        proxy.client.delete(key)
