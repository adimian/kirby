from redis import StrictRedis
from smart_getenv import getenv

from kirby.proxy.decoder import decode_bytes


ENCODING = "utf-8"


def _get_local_configuration():
    return {
        "host": getenv("REDIS_HOST", type=str),
        "port": getenv("REDIS_PORT", type=int),
        "password": getenv("REDIS_PASSWORD", type=str),
        "db": getenv("REDIS_DATABASE", type=str),
    }


class RedisProxy(object):
    def __init__(self, **kwargs):
        self.local_config = _get_local_configuration()
        self.client = self._create_redis_connection(**kwargs)

    def _create_redis_connection(self, **kwargs):
        return StrictRedis(**{**self.local_config, **kwargs})

    def set_value_with_ttl(self, key, value, time_to_live):
        self.client.set(key, value, ex=time_to_live, nx=True)
        print(
            f"REDIS - set key: {key} value: {value} for {time_to_live} seconds."
        )

    def get(self, key):
        response = self.client.get(key)

        return decode_bytes(response)
