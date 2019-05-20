import os
import json
from datetime import datetime
from pytest import fixture
from requests_flask_adapter import Session

from kirby.web import app_maker
from kirby.models import (
    db,
    Job,
    Environment,
    JobType,
    Context,
    Schedule,
    Notification,
    NotificationGroup,
)
from kirby.web.endpoints import test_schedule

BASE_API = "http://some-test-server.somewhere"


@fixture(scope="function")
def webapp():
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = app_maker(config=config)
    with app.app_context():
        db.create_all()
        yield app


@fixture
def session(webapp):
    Session.register(BASE_API, webapp)
    return Session()


@fixture
def current_schedule():
    with open(os.path.join("data", "schedule.json")) as fp:
        yield json.load(fp)


def test_it_compares_correctly_schedule_and_time():
    date = datetime(2019, 5, 20, 12, 0)
    assert test_schedule(Schedule(name="Every minute"), date)
    assert test_schedule(
        Schedule(
            name="At 12:00 on day-of-month 20", minute="0", hour="12", day="20"
        ),
        date,
    )
    assert not test_schedule(
        Schedule(name="Every minute past hour 13", hour="13"), date
    )


def init_schedule_on_db():
    test_env = Environment(name="test_env")

    admin_group = NotificationGroup(name="Admin")
    admin_group.add_email("admin@some-test-server.somewhere")
    producers_group = NotificationGroup(name="Producers")
    producers_group.add_email("producer1@some-test-server.somewhere")
    producers_group.add_email("producer2@some-test-server.somewhere")
    bakery_group = NotificationGroup(name="Bakery")
    bakery_group.add_email("bakery@some-test-server.somewhere")

    # First job
    baking_job = Job(name="Baking", type=JobType.SCHEDULED)
    baking_context = Context(
        environment=test_env,
        job=baking_job,
        package_name="baking",
        package_version="1.0.1",
    )

    schedule_every_minute = Schedule(name="every minute")
    baking_context.add_schedule(schedule_every_minute)

    first_notification_baking = Notification(
        on_retry=True, on_failure=True, job=baking_job, groups=[admin_group]
    )
    second_notification_baking = Notification(
        on_retry=False,
        on_failure=True,
        job=baking_job,
        groups=[producers_group, bakery_group],
    )

    # Second job
    realtime_job = Job(name="Insert Realtime", type=JobType.TRIGGERED)
    realtime_context = Context(
        environment=test_env,
        job=realtime_job,
        package_name="insert_realtime",
        package_version="2.1.0",
    )

    first_notification = Notification(
        on_retry=True, on_failure=True, job=realtime_job, groups=[admin_group]
    )

    # Job that mustn't appear

    stop_job = Job(name="Stop everything", type=JobType.SCHEDULED)
    stop_context = Context(
        environment=test_env,
        job=stop_job,
        package_name="shutdown",
        package_version="1.0.0",
    )

    db.session.add_all(
        [
            test_env,
            admin_group,
            producers_group,
            bakery_group,
            baking_job,
            baking_context,
            schedule_every_minute,
            first_notification_baking,
            second_notification_baking,
            realtime_job,
            realtime_context,
            first_notification,
            stop_job,
            stop_context,
        ]
    )
    db.session.commit()


def test_it_get_the_current_schedule(session, current_schedule):
    init_schedule_on_db()
    result = session.get("/".join([BASE_API, "schedule"]))
    result_json = result.json()

    actual_date = {"date": str(datetime.now())}
    result_json.update(actual_date)
    current_schedule.update(actual_date)

    assert result.status_code == 200
    assert result_json == current_schedule
