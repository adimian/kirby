import os
from freezegun import freeze_time
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock

from tests.tests_api.conftest import DATE

from kirby.models import db, Script, Topic
from kirby.api import Kirby, ClientError, ServerError


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


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_it_add_source(
    kirby_app, kirby_topic, db_scripts_not_registered, db_topics
):
    kirby_app.add_source(kirby_topic)

    script_in_db = get_script_in_db_from_id(kirby_app.ctx.ID)

    assert script_in_db.sources[0] == get_topic_in_db_from_name(
        kirby_topic.name
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    reason="missing KAFKA_BOOTSTRAP_SERVERS environment",
)
def test_it_add_destination(
    session, kirby_app, kirby_topic, db_scripts_not_registered, db_topics
):
    kirby_app.add_destination(kirby_topic)

    script_in_db = get_script_in_db_from_id(kirby_app.ctx.ID)

    assert script_in_db.destinations[0] == get_topic_in_db_from_name(
        kirby_topic.name
    )


def test_throw_error_if_bad_usage(kirby_app):
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


@patch("requests.session")
def test_throw_error_at_source_registration_if_error(
    session_mock, kirby_expected_env, kirby_hidden_env
):
    session_mock.return_value.get.side_effect = [
        MagicMock(
            status_code=500, json=MagicMock(return_value={"Server Error"})
        ),
        MagicMock(
            status_code=400, json=MagicMock(return_value={"Client Error"})
        ),
    ]
    session_mock.return_value.patch.return_value = MagicMock(
        status_code=200, json=MagicMock(return_value={})
    )

    kirby_app = Kirby(kirby_expected_env)
    with pytest.raises(ServerError):
        kirby_app.add_destination(MagicMock(id=1))
    with pytest.raises(ClientError):
        kirby_app.add_destination(MagicMock(id=-1))
