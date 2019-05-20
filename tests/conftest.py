from pytest import fixture
from datetime import datetime
from requests_flask_adapter import Session

from kirby.web import app_maker
from kirby.models import db, Environment, Job, Context, Script, Topic

API_ROOT = "http://some-test-server.somewhere"


@fixture(scope="function")
def webapp():
    app = app_maker(
        config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app


@fixture
def session(webapp):
    Session.register(API_ROOT, webapp)
    return Session()


@fixture
def db_env_factory():
    def _make_env(env_name):
        env = Environment(name=env_name)
        db.session.add(env)
        db.session.commit()
        return env

    yield _make_env


@fixture
def db_job_factory():
    def _make_job(job_name, job_type):
        job = Job(
            name=job_name,
            description=f"This job is named {job_name}.",
            type=job_type,
        )
        db.session.add(job)
        db.session.commit()
        return job

    yield _make_job


@fixture
def db_context_factory():
    def _make_context(env, job):
        context = Context(environment=env, job=job)
        db.session.add(context)
        db.session.commit()
        return context

    yield _make_context


@fixture
def db_script_factory():
    def _make_script(package_name, package_version, context):
        script = Script(
            package_name=package_name,
            package_version=package_version,
            context=context,
            first_seen=datetime.utcnow(),
        )
        db.session.add(script)
        db.session.commit()
        return script

    yield _make_script


@fixture
def db_topic_factory():
    def _make_topic(topic_name):
        topic = Topic(name=topic_name)
        db.session.add(topic)
        db.session.commit()
        return topic

    yield _make_topic
