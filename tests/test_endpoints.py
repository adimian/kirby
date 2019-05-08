from requests_flask_adapter import Session
from kirby.web import app_maker
from pytest import fixture

BASE_API = "http://localhost:5000"


@fixture
def session():
    app = app_maker()
    Session.register(BASE_API, app)
    return Session()


def test_it_register_a_job(session):
    result = session.post(
        "/".join([BASE_API, "registration"]),
        params={
            "name": "Test Scheduled",
            "description": "This is a test job.",
            "type": "scheduled",
        },
    )
    assert result.status_code == 200
    assert result.json() == {"id": 1}
