from redis import Redis
from time import sleep
from .election import Election


def run_supervisor(name, window):
    server = Redis()
    with Election(identity=name, server=server, check_ttl=window) as me:
        while True:
            if me.is_leader():
                print("I'm the leader!")
            else:
                print("I'm NOT the leader :(")

            sleep(2)
