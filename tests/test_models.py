import pytest
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

    context = Context(environment=test_env, package_name="my_script")
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
