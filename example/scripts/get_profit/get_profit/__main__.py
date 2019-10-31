import random
import time

from unittest import mock

WEBCLIENT_NAME = "DB/Profit"


def mocked_post(*args, **kargs):
    time.sleep(random.uniform(0.5, 1.5))
    print(f"posting {args}, {kargs}")


mocking_webclient = mock.patch("kirby.ext.webclient.WebClient").__enter__()
mocking_webclient.return_value.__enter__.return_value.name = WEBCLIENT_NAME
mocking_webclient.return_value.__enter__.return_value.post = mocked_post

if __name__ == "__main__":
    import kirby
    import datetime

    now = datetime.datetime.utcnow()
    today = datetime.datetime(
        year=now.year, month=now.month, day=now.day, minute=now.minute
    )
    half_a_day = datetime.timedelta(seconds=30)

    kirby_script = kirby.Kirby(
        {
            "PRODUCTION_TOPIC_NAME": {},
            "SALES_TOPIC_NAME": {},
            "PROFIT_API_BASE": {},
            "SURPLUS_TOPIC_NAME": {},
            "UNITARY_PRODUCTION_COST": {"type": int},
            "UNITARY_STORAGE_PRICE_PER_DAY": {"type": int},
            "UNITARY_SELLING_PRICE": {"type": int},
        }
    )
    context = kirby.context.ctx
    logger = kirby.log.Logger()

    with kirby.ext.topic.Topic(
        context.PRODUCTION_TOPIC_NAME, use_tls=False
    ) as production_topic:
        with kirby.ext.topic.Topic(
            context.SALES_TOPIC_NAME, use_tls=False
        ) as sales_topic:
            with kirby.ext.topic.Topic(
                context.SURPLUS_TOPIC_NAME, use_tls=False
            ) as surplus_topic:
                with kirby.ext.webclient.WebClient(
                    WEBCLIENT_NAME, context.PROFIT_API_BASE
                ) as profit_api:
                    kirby_script.add_source(production_topic)
                    kirby_script.add_source(sales_topic)
                    kirby_script.add_source(surplus_topic)
                    kirby_script.add_destination(profit_api)

                    profit = 0

                    profit -= (
                        production_topic.beetween(
                            today - half_a_day, today + half_a_day
                        )[0]
                        * context.PRODUCTION_COST
                    )

                    profit -= (
                        surplus_topic.beetween(
                            today - half_a_day, today + half_a_day
                        )[0]
                        * context.STORAGE_PRICE_PER_DAY
                    )

                    for sale in sales_topic.beetween(
                        today, today + 2 * half_a_day
                    ):
                        profit += sale * context.SELLING_PRICE

                    logger.info(f"Sending {profit}")
                    profit_api.post("/", data=profit)
