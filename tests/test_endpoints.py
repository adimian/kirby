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
    Script,
)
from kirby.web.endpoints import test_schedule

from tests.conftest import API_ROOT

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


def get_topic_id(session, name):
    return session.get(
        "/".join([API_ROOT, "topic"]), params={"name": name}
    ).json()["id"]


def test_if_get_topic_id(session, db_topic_factory):
    topic_name = "Orders"
    db_topic_factory(topic_name)
    assert get_topic_id(session, topic_name) == 1


def test_it_register_a_script(
    session,
    db_env_factory,
    db_job_factory,
    db_context_factory,
    db_script_factory,
    db_topic_factory,
):
    # Init variables to describe script env
    package_name = "booking_process"
    package_version = "1.0.1"
    orders_topic_name = "Orders"
    asset_management_topic_name = "AssetManagement"

    # Populate database
    env = db_env_factory("test")
    job = db_job_factory("Booking", JobType.TRIGGERED)
    context = db_context_factory(env, job)
    db_script_factory(package_name, package_version, context)
    db_topic_factory(orders_topic_name)
    db_topic_factory(asset_management_topic_name)

    # Get id registered
    id_source = get_topic_id(session, orders_topic_name)
    id_destination = get_topic_id(session, asset_management_topic_name)

    result = session.patch(
        "/".join([API_ROOT, "registration"]),
        params={
            "script_id": 1,
            "source_id": id_source,
            "destination_id": id_destination,
        },
    )
    assert result.status_code == 200

    script_registered = (
        db.session.query(Script).filter_by(package_name=package_name).one()
    )
    assert script_registered.sources[0].id == id_source
    assert script_registered.destinations[0].id == id_destination
