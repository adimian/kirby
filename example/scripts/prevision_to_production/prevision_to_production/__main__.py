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
            "PREVISION_TOPIC_NAME": {},
            "PRODUCTION_TOPIC_NAME": {},
            "PRODUCTION_API_BASE": {},
        }
    )
    context = kirby.context.ctx

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

                prevision = prevision_topic.next()(now - half_a_day, now)[-1]

                production_topic.post("/", data=prevision)
                production_api.post({"date": now, "qty": prevision})
