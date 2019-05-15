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


def init_schedule_on_db():
    test_env = Environment(name="test_env")

    admin_group = NotificationGroup(name="Admin")
    producers_group = NotificationGroup(name="Producers")
    bakery_group = NotificationGroup(name="Bakery")

    # First job
    baking_job = Job(name="Baking", type=JobType.SCHEDULED)
    baking_context = Context(
        environment=test_env,
        job=baking_job,
        package_name="baking",
        package_version="1.0.1",
    )

    every_ten_minute_schedule = Schedule(
        name="every ten minute", minute="/10", context=baking_context
    )
    baking_context.add_schedule(every_ten_minute_schedule)

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
    every_minute_schedule = Schedule(
        name="every minute", minute="/1", context=realtime_context
    )

    first_notification = Notification(
        on_retry=True, on_failure=True, job=realtime_job, groups=[admin_group]
    )

    db.session.add(test_env)
    db.session.add(admin_group)
    db.session.add(producers_group)
    db.session.add(bakery_group)
    db.session.add(baking_job)
    db.session.add(baking_context)
    db.session.add(every_ten_minute_schedule)
    db.session.add(first_notification_baking)
    db.session.add(second_notification_baking)
    db.session.add(realtime_job)
    db.session.add(realtime_context)
    db.session.add(every_minute_schedule)
    db.session.add(first_notification)
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
