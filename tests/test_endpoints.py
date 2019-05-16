from requests_flask_adapter import Session
from pytest import fixture
from datetime import datetime

from kirby.web import app_maker
from kirby.models import db, Environment, Job, JobType, Context, Script, Topic

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
def db_populated():
    env = Environment(name="test")
    job = Job(
        name="Booking",
        description="This is a process for booking orders.",
        type=JobType.TRIGGERED,
    )
    context = Context(environment=env, job=job)
    script = Script(
        package_name="booking_process",
        package_version="1.0.1",
        context=context,
        first_seen=datetime.utcnow(),
    )
    orders_topic = Topic(name="Orders")
    asset_management_topic = Topic(name="AssetManagement")

    db.session.add_all(
        [env, job, context, script, orders_topic, asset_management_topic]
    )
    db.session.commit()


def get_id_topic(session, name):
    return session.get(
        "/".join([BASE_API, "topic"]), params={"name": name}
    ).json()["id"]


def test_if_get_id_topic(session, db_populated):
    assert get_id_topic(session, "Orders") == 1


def test_it_register_a_script(session, db_populated):
    id_source = get_id_topic(session, "Orders")
    id_destination = get_id_topic(session, "AssetManagement")

    result = session.patch(
        "/".join([BASE_API, "registration"]),
        params={
            "script_id": 1,
            "source_id": id_source,
            "destination_id": id_destination,
        },
    )
    assert result.status_code == 200

    script_registered = (
        db.session.query(Script)
        .filter_by(package_name="booking_process")
        .one()
    )
    assert script_registered.sources[0].id == id_source
    assert script_registered.destinations[0].id == id_destination
