from flask import Flask
from ..models import db
from ..models.security import user_datastore, security
from .admin import admin
from .endpoints import api


def app_maker(config=None):
    app = Flask("kirby")

    if config:
        app.config.update(config)

    db.init_app(app)
    admin.init_app(app)
    api.init_app(app)
    security.init_app(app=app, datastore=user_datastore)

    @app.before_first_request
    def create_models():
        db.create_all()
        user_datastore.find_or_create_role("admin")

    return app
