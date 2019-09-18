import os
from freezegun import freeze_time
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock

from tests.tests_api.conftest import DATE, TOPIC_NAME

from kirby.models import db, Script, Topic
from kirby.api import Kirby, ClientError, ServerError
from kirby.api import ctx


def get_script_in_db_from_id(id_script):
    return db.session.query(Script).filter_by(id=id_script).one()


def get_topic_in_db_from_name(name_topic):
    return db.session.query(Topic).filter_by(name=name_topic).one()


@freeze_time(DATE)
def test_the_creation_of_a_kirby_app_by_testing_its_attribute(
    kirby_app, kirby_hidden_env
):
    script_in_db = get_script_in_db_from_id(ctx.ID)
    assert script_in_db.last_seen == datetime.utcnow()


def test_throw_error_if_wrong_id_on_registration(kirby_app):
    with pytest.raises(ClientError):
        kirby_app._register(source_id=-1, destination_id=-1)


@patch("requests.session")
def test_throw_error_at_init_if_server_error(
    session_mock, kirby_expected_env, kirby_hidden_env
):
    session_mock.return_value.patch.return_value = MagicMock(
        status_code=500, json=MagicMock(return_value={})
    )

    # Kirby register itself at init, at least to update 'last_seen' in the DB
    with pytest.raises(ServerError):
        Kirby(kirby_expected_env)


@pytest.mark.parametrize(
    "error_code, error_value, error_type",
    [(500, "Server Error", ServerError), (400, "Client Error", ClientError)],
)
@patch("requests.session")
def test_throw_error_at_destination_registration_if_error(
    session_mock,
    kirby_expected_env,
    kirby_hidden_env,
    error_code,
    error_value,
    error_type,
):
    session_mock.return_value.get.return_value = MagicMock(
        status_code=error_code, json=MagicMock(return_value={error_value})
    )
    session_mock.return_value.patch.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )

    kirby_app = Kirby(kirby_expected_env)
    with pytest.raises(error_type):
        kirby_app.add_destination(MagicMock(id=1))


@pytest.mark.parametrize(
    "error_code, error_value, error_type",
    [(500, "Server Error", ServerError), (400, "Client Error", ClientError)],
)
@patch("requests.session")
def test_throw_error_at_source_registration_if_error(
    session_mock,
    kirby_expected_env,
    kirby_hidden_env,
    error_code,
    error_value,
    error_type,
):
    session_mock.return_value.get.return_value = MagicMock(
        status_code=error_code, json=MagicMock(return_value={error_value})
    )
    session_mock.return_value.patch.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )
    kirby_app = Kirby(kirby_expected_env)
    with pytest.raises(error_type):
        kirby_app.add_source(MagicMock(id=1))


def test_it_raise_error_if_usage_of_testing_mode_with_get_topic_id():
    kirby_app = Kirby({}, testing=True)
    with pytest.raises(NotImplementedError):
        kirby_app.get_topic_id(topic_name="")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KIRBY_WEB_SERVER"),
    reason="missing KIRBY_WEB_SERVER environment",
)
def test_gets_the_id_of_a_topic(kirby_app, db_topics):
    topic = db_topics[0]
    assert kirby_app.get_topic_id(topic.name) == topic.id


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KIRBY_WEB_SERVER"),
    reason="missing KIRBY_WEB_SERVER environment",
)
def test_it_add_a_source_to_kirby_app_into_db_of_web_server(
    kirby_app, kirby_topic_factory, db_scripts_not_registered, db_topics
):
    with kirby_topic_factory(TOPIC_NAME) as kirby_topic:
        kirby_app.add_source(kirby_topic)

        script_in_db = get_script_in_db_from_id(ctx.ID)

        assert script_in_db.sources[0] == get_topic_in_db_from_name(
            kirby_topic.name
        )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KIRBY_WEB_SERVER"),
    reason="missing KIRBY_WEB_SERVER environment",
)
def test_it_add_a_destination_to_kirby_app_into_db_of_web_server(
    session,
    kirby_app,
    kirby_topic_factory,
    db_scripts_not_registered,
    db_topics,
):
    with kirby_topic_factory(TOPIC_NAME) as kirby_topic:
        kirby_app.add_destination(kirby_topic)

        script_in_db = get_script_in_db_from_id(ctx.ID)

        assert script_in_db.destinations[0] == get_topic_in_db_from_name(
            kirby_topic.name
        )
