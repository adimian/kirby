def mean(l):
    return int(sum(l) / len(l))


def test_new_day(now, last_day):
    # Since it's a proof of concept we don't test if it's a
    # new day but if it's a new minute
    return now.day != last_day


def percentage_advancement_in_the_day(now):
    # Return the percentage of time spent in the day
    # In the project a day is represented in a minute
    return now.second / 60


class Prevision:
    def __init__(self):
        self.sum_sales = kirby.context.ctx.INIT_QUANTITY
        self.nb_values = 1

    def get_prevision(self, sum_sales):
        prevision = self.get_temporary_prevision(sum_sales)
        self.nb_values += 1
        self.sum_sales += sum_sales
        return prevision

    def get_temporary_prevision(self, sum_sales):
        nb_values = self.nb_values + 1
        return (self.sum_sales + sum_sales) / nb_values


if __name__ == "__main__":
    import kirby
    import datetime

    kirby_script = kirby.Kirby(
        {
            "SALES_TOPIC_NAME": {},
            "PREVISION_TOPIC_NAME": {},
            "INIT_QUANTITY": {"type": int},
        }
    )
    context = kirby.context.ctx

    with kirby.ext.topic.Topic(
        context.SALES_TOPIC_NAME, use_tls=False
    ) as sales_topic:
        with kirby.ext.topic.Topic(
            context.PREVISION_TOPIC_NAME, use_tls=False
        ) as prevision_topic:

            kirby_script.add_source(sales_topic)
            kirby_script.add_destination(prevision_topic)

            # Init prevision for first production
            prevision_topic.send(context.INIT_QUANTITY)

            last_day = datetime.datetime.utcnow()
            prevision = Prevision()
            sales = []
            for sale in sales_topic:
                sales.append(sale)
                now = datetime.datetime.utcnow()

                if test_new_day(datetime.datetime.utcnow(), last_day):
                    # If a new day: get real prevision
                    last_day = now
                    prevision_topic.send(prevision.get_prevision(sum(sales)))
                    sales = []
                else:
                    # Else: temporary prevision
                    percentage = percentage_advancement_in_the_day(now)
                    estimation_sales_in_the_day = sum(sales) / percentage
                    prevision_topic.send(
                        prevision.get_temporary_prevision(
                            estimation_sales_in_the_day
                        )
                    )
