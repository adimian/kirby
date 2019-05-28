from freezegun import freeze_time
from datetime import datetime
from pytest import raises, fixture

from tests.tests_api.conftest import DATE, TOPIC_NAME

from kirby.models import db, Script, Topic


@fixture(scope="function")
def kirby_topic(kirby_topic_factory):
    return kirby_topic_factory(TOPIC_NAME)


def get_script_in_db_from_id(id_script):
    return db.session.query(Script).filter_by(id=id_script).one()


def get_topic_in_db_from_name(name_topic):
    return db.session.query(Topic).filter_by(name=name_topic).one()


@freeze_time(DATE)
def test_it_create_a_kirby_app(kirby_app, kirby_hidden_env):
    assert (
        kirby_app.ctx.WEBCLIENT_ENDPOINT
        == kirby_hidden_env["WEBCLIENT_ENDPOINT"]
    )

    script_in_db = get_script_in_db_from_id(kirby_app.ctx.ID)
    assert script_in_db.last_seen == datetime.utcnow()


def test_it_add_source(
    session, kirby_app, kirby_topic, db_scripts_not_registered, db_topics
):
    kirby_app.add_source(kirby_topic)

    script_in_db = get_script_in_db_from_id(kirby_app.ctx.ID)

    assert script_in_db.sources[0] == get_topic_in_db_from_name(
        kirby_topic.topic_name
    )


def test_it_add_destination(
    session, kirby_app, kirby_topic, db_scripts_not_registered, db_topics
):
    kirby_app.add_destination(kirby_topic)

    script_in_db = get_script_in_db_from_id(kirby_app.ctx.ID)

    assert script_in_db.destinations[0] == get_topic_in_db_from_name(
        kirby_topic.topic_name
    )


def test_throw_error_if_bad_usage(kirby_app):
    with raises(ValueError) as excinfo:
        kirby_app._register({"bad_key": 1})
    assert "'source_id' and 'destination_id'" in str(
        excinfo.value
    ), f"The function should not accept this key"
