import pytest
from datetime import datetime
from dateutil.parser import parse
from kirby.models import (
    db,
    Job,
    Environment,
    JobType,
    Context,
    Schedule,
    Suspension,
    NotificationGroup,
    Script,
    Topic,
)
from kirby.web import app_maker


@pytest.fixture(scope="function")
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


def test_it_creates_a_job(webapp):

    job = Job(
        name="retrieve cash register data",
        description="connects to the cash register API and fetches latest sale",
        type=JobType.SCHEDULED,
    )

    test_env = Environment(name="test")

    context = Context(environment=test_env)
    context.set_config(url="http://localhost:8000", loop=30, retry=True)

    schedule = Schedule(name="every two minutes", hour="*", minute="/2")
    context.add_schedule(schedule)

    suspension = Suspension(start=parse("2019-01-01"), end=parse("2019-01-02"))
    schedule.add_suspension(suspension)

    group = NotificationGroup(name="admins")
    group.add_email("admin@local.local")

    job.add_context(context)
    job.add_notification(group, on_retry=True, on_failure=True)

    db.session.add(job)
    db.session.commit()

    assert (
        job.notifications[0].groups[0].emails[0].email == "admin@local.local"
    )


def test_it_creates_a_script(webapp):
    test_env = Environment(name="test_env")
    db.session.add(test_env)
    job = Job(
        name="retrieve cash register data",
        description="connects to the cash register API and fetches latest sale",
        type=JobType.SCHEDULED,
    )
    db.session.add(job)

    context = Context(environment=test_env, job=job)

    schedule = Schedule(name="every two minutes", hour="*", minute="/2")
    db.session.add(schedule)
    context.add_schedule(schedule)
    db.session.add(context)

    script = Script(
        context=context,
        package_name="test_package",
        package_version="0.0.1",
        first_seen=datetime.now(),
    )

    source = Topic(name="source")
    db.session.add(source)
    destination = Topic(name="destination")
    db.session.add(destination)
    script.add_source(source)
    script.add_destination(destination)

    db.session.add(script)
    db.session.commit()

    db.session.query()

    assert script.sources == [source]
    assert script.destinations == [destination]
    assert script.context.environment.name == "test_env"
    assert script.context.job.name == "retrieve cash register data"
    assert script.context.schedules[0].name == "every two minutes"
