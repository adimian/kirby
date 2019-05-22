from freezegun import freeze_time
from datetime import datetime

from tests.tests_api.conftest import DATE

from kirby.models import db, Script


@freeze_time(DATE)
def test_it_create_a_kirby_app(kirby_app, kirby_hidden_env):
    assert (
        kirby_app.ctx.WEBCLIENT_ENDPOINT
        == kirby_hidden_env["WEBCLIENT_ENDPOINT"]
    )

    script_in_db = (
        db.session.query(Script).filter_by(id=kirby_app.ctx.ID).one()
    )
    assert script_in_db.last_seen == datetime.utcnow()
