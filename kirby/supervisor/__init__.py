from redis import Redis
from time import sleep
from .election import Election
from time import perf_counter

import logging

logger = logging.getLogger(__name__)


def run_supervisor(name, window, wakeup):
    server = Redis()
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            checkpoint = perf_counter()
            if me.is_leader():
                print("I'm the leader!")
            else:
                print("I'm NOT the leader :(")

            drift = perf_counter() - checkpoint
            next_wakeup = wakeup - drift
            logger.debug("waking up in {:.2f}s".format(next_wakeup))
            sleep(next_wakeup)
