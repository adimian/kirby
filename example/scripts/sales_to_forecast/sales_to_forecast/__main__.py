def mean(l):
    return int(sum(l) / len(l))


def test_new_day(now, last_day):
    # Since it's a proof of concept we don't test if it's a
    # new day but if it's a new minute

    return now.replace(microsecond=0).replace(second=0) != last_day.replace(
        microsecond=0
    ).replace(second=0)


def percentage_advancement_in_the_day(now):
    # Return the percentage of time spent in the day
    # In the project a day is represented in a minute
    return now.second / 60


class Forecast:
    def __init__(self):
        self.sum_sales = kirby.context.ctx.INIT_QUANTITY
        self.nb_values = 1

    def get_forecast(self, sum_sales):
        forecast = self.get_temporary_forecast(sum_sales)
        self.nb_values += 1
        self.sum_sales += sum_sales
        return forecast

    def get_temporary_forecast(self, sum_sales):
        nb_values = self.nb_values + 1
        return (self.sum_sales + sum_sales) / nb_values


if __name__ == "__main__":
    import kirby
    import datetime

    kirby_script = kirby.Kirby(
        {
            "SALES_TOPIC_NAME": {},
            "FORECAST_TOPIC_NAME": {},
            "INIT_QUANTITY": {"type": int},
        }
    )
    context = kirby.context.ctx
    logger = kirby.log.Logger()
    with kirby.ext.topic.Topic(
        context.SALES_TOPIC_NAME, use_tls=False
    ) as sales_topic:
        with kirby.ext.topic.Topic(
            context.FORECAST_TOPIC_NAME, use_tls=False
        ) as forecast_topic:

            kirby_script.add_source(sales_topic)
            kirby_script.add_destination(forecast_topic)

            # Init forecast for first production
            forecast_topic.send(context.INIT_QUANTITY)

            last_day = datetime.datetime.utcnow()
            forecast = Forecast()
            sales = []
            # First forecast
            forecast_topic.send("150")

            for sale in sales_topic:
                sales.append(int(sale))
                now = datetime.datetime.utcnow()

                if test_new_day(datetime.datetime.utcnow(), last_day):
                    # If a new day: get real forecast
                    last_day = now
                    logger.info(f"sum_sales {sum(sales)}")

                    logger.info(
                        f" forecast {forecast.get_forecast(sum(sales))}"
                    )

                    forecast_topic.send(forecast.get_forecast(sum(sales)))
                    sales = []
                else:
                    # Else: temporary forecast
                    percentage = percentage_advancement_in_the_day(now)
                    estimation_sales_in_the_day = sum(sales) / percentage
                    logger.info(
                        f"estimation_sales_in_the_day {estimation_sales_in_the_day}"
                    )
                    # forecast.send(
                    #     forecast.get_temporary_forecast(
                    #         estimation_sales_in_the_day
                    #     )
                    # )
