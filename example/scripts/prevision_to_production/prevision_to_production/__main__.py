import example_utils


from time import sleep

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
            "PREVISION_TOPIC_NAME": {},
            "PRODUCTION_TOPIC_NAME": {},
            "PRODUCTION_API_BASE": {},
        }
    )
    context = kirby.context.ctx
    logger = kirby.log.Logger()

    with kirby.ext.topic.Topic(
        context.PREVISION_TOPIC_NAME, use_tls=False
    ) as prevision_topic:
        with kirby.ext.topic.Topic(
            context.PRODUCTION_TOPIC_NAME, use_tls=False
        ) as production_topic:
            with kirby.ext.webclient.WebClient(
                WEBCLIENT_NAME, context.PRODUCTION_API_BASE
            ) as production_api:
                kirby_script.add_source(prevision_topic)
                kirby_script.add_destination(production_topic)
                kirby_script.add_destination(production_api)
                prevision_found = False
                logger.info(f"While loop ")
                while not prevision_found:
                    previsions = prevision_topic.between(
                        today, today + 2 * half_a_day
                    )
                    if len(previsions) != 0:
                        prevision = previsions[-1]
                        prevision_found = True
                    else:
                        logger.info(
                            f"no message found between {today} and {today+ 2 * half_a_day} "
                        )
                        sleep(5)

                logger.info(f"Sending {prevision}")
                production_topic.send(str(prevision))
                production_api.post({"date": now, "qty": prevision})
