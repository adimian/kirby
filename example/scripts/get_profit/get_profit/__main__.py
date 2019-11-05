import example_utils

WEBCLIENT_NAME = "DB/Profit"


example_utils.mock_webclient(WEBCLIENT_NAME)

if __name__ == "__main__":
    import kirby
    import datetime

    now = datetime.datetime.utcnow()
    today = datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
    )
    half_a_day = datetime.timedelta(seconds=30)

    kirby_script = kirby.Kirby(
        {
            "PRODUCTION_TOPIC_NAME": {},
            "SALES_TOPIC_NAME": {},
            "PROFIT_API_BASE": {},
            "SURPLUS_TOPIC_NAME": {},
            "UNITARY_PRODUCTION_COST": {"type": float},
            "UNITARY_STORAGE_PRICE_PER_DAY": {"type": float},
            "UNITARY_SELLING_PRICE": {"type": float},
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

                    current_productions = production_topic.between(
                        today - half_a_day, today + half_a_day
                    )
                    if len(current_productions) != 0:
                        current_production = current_productions[-1]
                    else:
                        current_production = 0
                    profit -= (
                        current_production * context.UNITARY_PRODUCTION_COST
                    )

                    profit -= (
                        current_production
                        * context.UNITARY_STORAGE_PRICE_PER_DAY
                    )

                    for sale in sales_topic.between(
                        today, today + 2 * half_a_day
                    ):
                        profit += sale * context.UNITARY_SELLING_PRICE

                    logger.info(f"Sending {profit}")
                    profit_api.post("/", data=profit)
