from kirby.models import db, JobType, Script

from tests.conftest import API_ROOT


def get_id_topic(session, name):
    return session.get(
        "/".join([API_ROOT, "topic"]), params={"name": name}
    ).json()["id"]


def test_if_get_id_topic(session, db_topic_factory):
    topic_name = "Orders"
    db_topic_factory(topic_name)
    assert get_id_topic(session, topic_name) == 1


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
    id_source = get_id_topic(session, orders_topic_name)
    id_destination = get_id_topic(session, asset_management_topic_name)

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
