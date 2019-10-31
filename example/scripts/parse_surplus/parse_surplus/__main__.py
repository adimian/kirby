import random
import time

from unittest import mock


WEBCLIENT_NAME = "DB/Stock"


def mocked_update(*args, **kargs):
    time.sleep(random.uniform(0.5, 1.5))
    print(f"updating {args}, {kargs}")


mocking_webclient = mock.patch("kirby.ext.webclient.WebClient").__enter__()
mocking_webclient.return_value.__enter__.return_value.name = WEBCLIENT_NAME
mocking_webclient.return_value.__enter__.return_value.update = mocked_update

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
            "SURPLUS_TOPIC_NAME": {},
            "STOCK_API_BASE": {},
        }
    )
    context = kirby.context.ctx

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
                    WEBCLIENT_NAME, context.STOCK_API_BASE
                ) as stock_api:
                    kirby_script.add_source(production_topic)
                    kirby_script.add_source(sales_topic)
                    kirby_script.add_destination(surplus_topic)

                    surplus = surplus_topic.beetween(
                        today - half_a_day, today + half_a_day
                    )
                    if len(surplus) > 0:
                        last_surplus_qty = surplus[0]
                    else:
                        last_surplus_qty = 0

                    produced_qty = production_topic.beetween(
                        today - half_a_day, today + half_a_day
                    )[0]

                    sold_qty = sum(
                        surplus_topic.beetween(today, today + 2 * half_a_day)
                    )

                    surplus_qty = (produced_qty - sold_qty) + last_surplus_qty

                    surplus_topic.send(surplus_qty)
                    stock_api.update("/", data=surplus_qty)
