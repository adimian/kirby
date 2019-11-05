import os

import kirby
from kirby import models
from example.populate_database import create_example_db, read_json
from kirby.models import db
from kirby.web import app_maker

DEMO_JSON_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "example", "demo.json"
)


def test_read_json():
    env_dict, env_var_dict, job_dict, ext_list, user_list, notification_group_dict = read_json(
        DEMO_JSON_FILE_PATH
    )
    assert env_dict == {"test": "Test", "dev": "Development", "prod": "Prod"}
    assert env_var_dict == {
        models.ConfigScope.GLOBAL: {
            "KAFKA_BOOTSTRAP_SERVERS": "http://localhost:9092",
            "KIRBY_WEB_SERVER": "http://localhost:8080",
            "KAFKA_USE_TLS": False,
            "UNITARY_PRODUCTION_COST": 0.8,
            "UNITARY_STORAGE_PRICE_PER_DAY": 0.2,
            "UNITARY_SELLING_PRICE": 1.5,
        }
    }
    assert job_dict == {
        "sensor_sales": {
            "description": "Fetch sales",
            "type": models.JobType.DAEMON,
            "package_version": {
                "test": "0.0.1",
                "dev": "0.1.0",
                "prod": "1.0.0",
            },
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {"SALES_TOPIC_NAME": "sales"},
                models.ConfigScope.CONTEXT: {
                    "test": {"SALES_API_BASE": "localhost:8000"},
                    "dev": {
                        "SALES_API_BASE": "http://some.server.somewhere:8000"
                    },
                    "prod": {
                        "SALES_API_BASE": "http://some.server.elsewhere:8000"
                    },
                },
            },
        },
        "sales_to_prevision": {
            "description": "Process sales to estimate prevision",
            "type": models.JobType.DAEMON,
            "package_version": {
                "test": "0.0.1",
                "dev": "0.1.0",
                "prod": "1.0.0",
            },
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {
                    "INIT_QUANTITY": 50,
                    "SALES_TOPIC_NAME": "sales",
                    "PREVISION_TOPIC_NAME": "prevision",
                },
                models.ConfigScope.CONTEXT: {
                    "test": {},
                    "dev": {},
                    "prod": {},
                },
            },
        },
        "prevision_to_production": {
            "description": "Set production as prevision",
            "type": models.JobType.SCHEDULED,
            "scheduled_param": {
                "name": "schedule for prevision_to_production",
                "hour": "*",
                "minute": "*",
            },
            "package_version": {
                "test": "0.0.1",
                "dev": "0.1.0",
                "prod": "1.0.0",
            },
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {
                    "PREVISION_TOPIC_NAME": "prevision",
                    "PRODUCTION_TOPIC_NAME": "production",
                },
                models.ConfigScope.CONTEXT: {
                    "dev": {
                        "PRODUCTION_API_BASE": "http://some.server.somewhere:8000"
                    },
                    "prod": {
                        "PRODUCTION_API_BASE": "http://some.server.elsewhere:8000"
                    },
                    "test": {"PRODUCTION_API_BASE": "localhost:8000"},
                },
            },
        },
        "parse_surplus": {
            "description": "Compare production and sales to get the surplus",
            "type": models.JobType.SCHEDULED,
            "scheduled_param": {
                "name": "schedule for parse_surplus",
                "hour": "*",
                "minute": "*",
            },
            "package_version": {
                "test": "0.0.1",
                "dev": "0.1.0",
                "prod": "1.0.0",
            },
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {
                    "PRODUCTION_TOPIC_NAME": "production",
                    "SALES_TOPIC_NAME": "sales",
                    "SURPLUS_TOPIC_NAME": "surplus",
                },
                models.ConfigScope.CONTEXT: {
                    "test": {"STOCK_API_BASE": "localhost:8000"},
                    "dev": {
                        "STOCK_API_BASE": "http://some.server.somewhere:8000"
                    },
                    "prod": {
                        "STOCK_API_BASE": "http://some.server.elsewhere:8000"
                    },
                },
            },
        },
        "get_profit": {
            "description": "Calculates profit from sales, production and surplus",
            "type": models.JobType.DAEMON,
            "package_version": {
                "test": "0.0.1",
                "dev": "0.1.0",
                "prod": "1.0.0",
            },
            "notification_group": "sysadmins",
            "config": {
                models.ConfigScope.JOB: {
                    "PRODUCTION_TOPIC_NAME": "production",
                    "SALES_TOPIC_NAME": "sales",
                    "SURPLUS_TOPIC_NAME": "surplus",
                },
                models.ConfigScope.CONTEXT: {
                    "test": {"PROFIT_API_BASE": "localhost:8000"},
                    "dev": {
                        "PROFIT_API_BASE": "http://some.server.somewhere:8000"
                    },
                    "prod": {
                        "PROFIT_API_BASE": "http://some.server.elsewhere:8000"
                    },
                },
            },
        },
    }
    assert ext_list == [
        "DB/Sales",
        "DB/Stock",
        "DB/Profit",
        "DB/Production",
        "sales",
        "prevision",
        "production",
        "surplus",
    ]
    assert user_list == [
        {"username": "demo", "password": "demo", "role": "admin"}
    ]
    assert notification_group_dict == {"sysadmins": []}


def test_create_demo_db():
    db_temp_file = "test.db"
    os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_temp_file}"
    app = app_maker()
    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_example_db(db.session, DEMO_JSON_FILE_PATH)
    os.remove(os.path.join(os.path.dirname(kirby.__file__), db_temp_file))
