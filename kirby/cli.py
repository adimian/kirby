def web():
    from kirby.web import app_maker

    config = {
        "TESTING": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///kirby.db",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }

    app = app_maker(config=config)

    app.run(debug=True, port="5000")
