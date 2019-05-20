import uuid

from smart_getenv import getenv

from kirby.proxy.redis_proxy import RedisProxy


class Consensus(object):
    def __init__(self, unique_identifier=None):
        self.redis_proxy = RedisProxy()
        self.unique_identifier = unique_identifier or str(uuid.uuid4())

        self.time_to_live = getenv("REDIS_LEADER_TTL", type=int)
        self.leader_key = getenv("REDIS_LEADER_KEY", type=str)

    def is_leader(self):
        is_leader = False

        self.redis_proxy.set_value_with_ttl(
            self.leader_key, self.unique_identifier, self.time_to_live
        )
        elected_leader = self.redis_proxy.get(self.leader_key)
        if elected_leader:
            is_leader = self.unique_identifier == elected_leader

        return is_leader
