import random
import time

from unittest import mock


WEBCLIENT_NAME = "DB/Sales"


def mocked_get(*args, **kargs):
    time.sleep(random.uniform(0.5, 1.5))
    return random.randint(1, 10)


mocking_webclient = mock.patch("kirby.ext.webclient.WebClient").__enter__()
mocking_webclient.return_value.__enter__.return_value.name = WEBCLIENT_NAME
mocking_webclient.return_value.__enter__.return_value.get = mocked_get


if __name__ == "__main__":
    import kirby

    kirby_script = kirby.Kirby(
        {
            "SALES_TOPIC_NAME": {},
            "SALES_API_BASE": {},
            "UNITARY_PRODUCTION_COST": {"type": int},
            "UNITARY_STORAGE_PRICE_PER_DAY": {"type": int},
            "UNITARY_SELLING_PRICE": {"type": int},
        }
    )
    context = kirby.context.ctx

    with kirby.ext.webclient.WebClient(
        WEBCLIENT_NAME, context.SALES_API_BASE
    ) as sales_api:
        with kirby.ext.topic.Topic(
            context.SALES_TOPIC_NAME, use_tls=False
        ) as sales_topic:
            kirby_script.add_source(sales_api)
            kirby_script.add_destination(sales_topic)

            while True:
                sales_topic.send(sales_api.get("/"))
                time.sleep(random.randrange(1, 3))
