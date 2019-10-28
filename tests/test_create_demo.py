import os

import kirby
from kirby import models
from example.populate_database import create_example_db, read_json
from kirby.models import db
from kirby.web import app_maker

DEMO_JSON_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "example", "short_demo.json"
)


def test_read_json():
    env_dict, env_var_dict, job_dict, ext_list, user_list, notification_group_dict = read_json(
        DEMO_JSON_FILE_PATH
    )
    assert env_dict == {"dev": "Development"}
    assert env_var_dict == {
        models.ConfigScope.GLOBAL: {
            "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
            "KIRBY_WEB_SERVER": "localhost:8080",
        }
    }
    assert job_dict == {
        "sensorcash": {
            "description": "cashregister daemon (from bakery API to cashregister topic)",
            "type": models.JobType.DAEMON,
            "package_version": {"dev": "0.1"},
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {
                    "CASHREGISTER_TOPIC_NAME": "cashregister",
                    "BAKERY_API_BASE": "http://127.0.0.1:8000",
                    "CASHREGISTER_ENDPOINT": "sales/cashregister",
                },
                models.ConfigScope.CONTEXT: {
                    "dev": {},
                    "test": {},
                    "prod": {},
                },
            },
        },
        "realtime": {
            "description": "create total files (from  cashregister topic to totalfiles)",
            "type": models.JobType.SCHEDULED,
            "package_version": {"dev": "0.1"},
            "notification_group": "sysadmins",
            "scheduled_param": {
                "name": "every two minutes",
                "hour": "*",
                "minute": "*/2",
            },
            "config": {
                models.ConfigScope.JOB: {
                    "CASHREGISTER_TOPIC_NAME": "cashregister",
                    "TOTAL_FILES_FOLDER_PATH": "realtime_totals",
                },
                models.ConfigScope.CONTEXT: {
                    "dev": {},
                    "test": {},
                    "prod": {},
                },
            },
        },
    }
    assert ext_list == ["bakery", "cashregister", "totalfiles"]
    assert user_list == [
        {"username": "demo", "password": "demo", "role": "admin"}
    ]
    assert notification_group_dict == {"sysadmins": ["alice@local.local"]}


def test_create_demo_db():
    db_temp_file = "test.db"
    os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_temp_file}"
    app = app_maker()
    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_example_db(db.session, DEMO_JSON_FILE_PATH)
    os.remove(os.path.join(os.path.dirname(kirby.__file__), db_temp_file))
