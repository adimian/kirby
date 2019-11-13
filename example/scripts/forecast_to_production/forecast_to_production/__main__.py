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
    one_day = datetime.timedelta(minutes=1)

    kirby_script = kirby.Kirby(
        {
            "FORECAST_TOPIC_NAME": {},
            "PRODUCTION_TOPIC_NAME": {},
            "PRODUCTION_API_BASE": {},
        }
    )
    context = kirby.context.ctx
    logger = kirby.log.Logger()

    logger.log("Start")
    with kirby.ext.topic.Topic(
        context.FORECAST_TOPIC_NAME, use_tls=False
    ) as forecast_topic:
        with kirby.ext.topic.Topic(
            context.PRODUCTION_TOPIC_NAME, use_tls=False
        ) as production_topic:
            with kirby.ext.webclient.WebClient(
                WEBCLIENT_NAME, context.PRODUCTION_API_BASE
            ) as production_api:
                kirby_script.add_source(forecast_topic)
                kirby_script.add_destination(production_topic)
                kirby_script.add_destination(production_api)

                forecast_found = False
                while not forecast_found:
                    forecasts = forecast_topic.between(today, today + one_day)
                    if len(forecasts) != 0:
                        forecast = forecasts[-1]
                        forecast_found = True
                    else:
                        logger.debug(
                            f"no message found between "
                            f"{today} and {today + one_day} "
                        )
                        sleep(0.5)

                logger.info(f"Sending forecast={forecast}")
                production_topic.send(str(forecast))
                production_api.post({"date": now, "qty": forecast})

    logger.log("Finished")
