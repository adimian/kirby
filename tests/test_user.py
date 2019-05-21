from kirby.models.security import user_datastore
from kirby.models import db


def test_create_user(webapp):
    user = user_datastore.create_user(
        username="admin", email="admin@local.local", password="password"
    )
    db.session.commit()

    assert user.is_local
    assert not user.is_admin


def test_promote_user_to_admin(webapp):

    user = user_datastore.create_user(
        username="admin", email="admin@local.local", password="password"
    )
    role = user_datastore.find_role("admin")
    assert role

    db.session.commit()

    assert not user.is_admin

    user_datastore.add_role_to_user(role=role, user=user)

    db.session.commit()

    assert user.is_admin
