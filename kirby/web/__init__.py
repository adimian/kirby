from flask import Flask, url_for
from flask_admin import helpers as admin_helpers
from smart_getenv import getenv

from .admin import admin
from .endpoints import api
from .forms import LoginForm
from ..models import db
from ..models.security import user_datastore, security, UserRoles


def app_maker(config=None):
    app = Flask("kirby")

    app.config["TESTING"] = getenv("TESTING", type=bool)
    app.config["SQLALCHEMY_DATABASE_URI"] = getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = getenv(
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    )
    app.config["SECRET_KEY"] = getenv("SECRET_KEY")
    app.config["SECURITY_PASSWORD_SALT"] = getenv("SECURITY_PASSWORD_SALT")

    if config:  # pragma: no cover
        app.config.update(config)

    db.init_app(app)
    admin.init_app(app)
    api.init_app(app)
    security._state = security.init_app(
        app=app, datastore=user_datastore, login_form=LoginForm
    )

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for,
        )

    @app.before_first_request
    def create_models():
        db.create_all()
        user_datastore.find_or_create_role(UserRoles.ADMIN.value)
        db.session.commit()

    return app
