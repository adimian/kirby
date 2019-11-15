import random
import time
from time import sleep

import example_utils


WEBCLIENT_NAME = "DB/Sales"


def mocked_get(*args, **kargs):
    time.sleep(random.uniform(0.5, 1.5))
    return random.randint(1, 10)


example_utils.mock_webclient(WEBCLIENT_NAME, get=mocked_get)


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
    logger = kirby.log.Logger(default_level="debug")

    with kirby.ext.webclient.WebClient(
        WEBCLIENT_NAME, context.SALES_API_BASE
    ) as sales_api:
        with kirby.ext.topic.Topic(
            context.SALES_TOPIC_NAME, use_tls=False
        ) as sales_topic:
            kirby_script.add_source(sales_api)
            kirby_script.add_destination(sales_topic)
            sleep(60)
            while True:
                sale = sales_api.get("/")
                logger.info(f"Sending {sale}")
                sales_topic.send(str(sale))
                time.sleep(random.randrange(1, 3))
