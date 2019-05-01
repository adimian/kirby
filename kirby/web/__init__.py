from flask import Flask
from ..models import db
from .admin import admin


def app_maker(config=None):
    app = Flask("kirby")

    if config:
        app.config.update(config)

    db.init_app(app)
    admin.init_app(app)

    @app.before_first_request
    def create_models():
        db.create_all()

    return app
