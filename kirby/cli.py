from dotenv import load_dotenv

load_dotenv()

from getpass import getpass

import click

from kirby.demo import create_demo_db
from kirby.models import db
from kirby.models.security import user_datastore
from kirby.supervisor import run_supervisor
from kirby.web import app_maker
from smart_getenv import getenv

import logging

DEFAULT_LOG_FORMAT = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"


logging.basicConfig(
    level=logging.DEBUG,
    format=getenv("LOG_FORMAT", default=DEFAULT_LOG_FORMAT),
)
logging.getLogger("kafka").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


def read_topic(name):
    """
    debug function to consume the messages in a kafka topic
    :param name: name of the topic
    """
    from kafka import KafkaConsumer
    import msgpack
    import json
    from pprint import pformat

    bootstrap_servers = getenv(
        "KAFKA_BOOTSTRAP_SERVERS", type=list, separator=","
    )
    consumer = KafkaConsumer(
        name,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=msgpack.loads,
    )

    for idx, message in enumerate(consumer, start=1):
        message = message.value
        try:
            message = json.loads(message.decode("utf-8"))
            logger.debug(pformat(message))
        except Exception:
            logger.debug(message)


@click.command()
@click.option(
    "--host", type=str, default="127.0.0.1", help="The interface to bind to"
)
@click.option("--port", type=str, default="8080", help="The port to bind to")
@click.option("--debug", type=bool, default=False, help="Start in DEBUG mode")
def web(host, port, debug):
    app = app_maker()
    app.run(debug=debug, port=port, host=host)


@click.command()
@click.argument("username")
def adduser(username):
    app = app_maker()

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        user = user_datastore.find_user(username=username)
        if user is None:
            user = user_datastore.create_user(
                username=username, password=getpass()
            )

        msg = ""
        if click.confirm("Give admin rights?"):
            msg = "with admin rights"
            role = user_datastore.find_role("admin")
            user_datastore.add_role_to_user(user=user, role=role)

        click.echo(f"User {username} added {msg}")
        db.session.commit()


@click.command()
@click.argument("name")
@click.option(
    "--window",
    type=int,
    default=5,
    help="Leader election window size (in seconds)",
)
@click.option(
    "--wakeup",
    type=int,
    default=30,
    help="Shortest time interval between two scheduler executions",
)
def supervisor(name, window, wakeup):
    run_supervisor(name, window, wakeup)


@click.command()
def demo():
    app = app_maker()

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_demo_db(db.session)

    click.echo("demo data inserted in the database")


@click.group()
def debug():
    pass


@click.command()
@click.argument("name")
def dump(name):
    read_topic(name)


debug.add_command(dump)


@click.group()
def cli():
    pass


cli.add_command(web)
cli.add_command(adduser)
cli.add_command(supervisor)
cli.add_command(demo)
cli.add_command(debug)


if __name__ == "__main__":
    cli()
