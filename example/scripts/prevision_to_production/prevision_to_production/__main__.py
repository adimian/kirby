import example_utils


WEBCLIENT_NAME = "DB/Profit"


example_utils.mock_webclient(WEBCLIENT_NAME)

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
            context.PREVISION_TOPIC_NAME, use_tls=False
        ) as production_topic:
            with kirby.ext.webclient.WebClient(
                WEBCLIENT_NAME, context.PRODUCTION_API_BASE
            ) as production_api:
                kirby_script.add_source(prevision_topic)
                kirby_script.add_destination(production_topic)
                kirby_script.add_destination(production_api)

                prevision = prevision_topic.between(now - half_a_day, now)[-1]

                logger.info(f"Sending {prevision}")
                production_topic.send(prevision)
                production_api.post({"date": now, "qty": prevision})
