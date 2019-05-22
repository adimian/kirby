from datetime import datetime
from freezegun import freeze_time

from kirby.models import db, Schedule, Script
from kirby.web.endpoints import should_run

from tests.conftest import API_ROOT


def test_it_compares_correctly_schedule_and_time():
    date = datetime(2019, 5, 20, 12, 0)
    assert should_run(Schedule(name="Every minute"), date)
    assert should_run(
        Schedule(
            name="At 12:00 on day-of-month 20", minute="0", hour="12", day="20"
        ),
        date,
    )
    assert not should_run(
        Schedule(name="Every minute past hour 13", hour="13"), date
    )


def test_it_get_the_current_schedule(session, db_scripts_registered):
    result = session.get("/".join([API_ROOT, "schedule"]))
    result_json = result.json()

    assert result.status_code == 200
    assert result_json["jobs"][0]["environment"] == "test_env"


def get_topic_id(session, name):
    response = session.get(
        "/".join([API_ROOT, "topic"]), params={"name": name}
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_if_get_topic_id(session, db_topics):
    for i, topic in enumerate(db_topics, start=1):
        assert get_topic_id(session, topic.name) == i


@freeze_time("2019-05-20 15:34")
def test_it_register_a_script(session, db_scripts_not_registered, db_topics):
    id_source = get_topic_id(session, "orders")
    id_destination = get_topic_id(session, "asset_management")

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
        db.session.query(Script)
        .filter_by(package_name="orders_retriever")
        .one()
    )
    assert script_registered.sources[0].id == id_source
    assert script_registered.destinations[0].id == id_destination


def test_schedule_contains_configuration(session, db_scripts_registered):
    script = (
        db.session.query(Script)
        .filter_by(package_name="orders_retriever")
        .one()
    )

    context = script.context
    context.set_config(API_USERNAME="test-user", API_PORT=2000)

    result = session.get("/".join([API_ROOT, "schedule"]))
    result_json = result.json()

    assert result.status_code == 200
    assert result_json["jobs"][0]["variables"] == [
        {"key": "API_USERNAME", "value": "test-user"},
        {"key": "API_PORT", "value": "2000"},
    ]
