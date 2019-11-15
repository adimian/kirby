import click
import logging

from dotenv import load_dotenv
from getpass import getpass
from smart_getenv import getenv

from kirby.models import db
from kirby.models.security import user_datastore
from kirby.supervisor import run_supervisor
from kirby.web import app_maker

load_dotenv()
DEFAULT_LOG_FORMAT = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"

logging.basicConfig(
    level=logging.INFO,
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
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
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
@click.option(
    "--log_level",
    type=click.Choice(
        ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"],
        case_sensitive=False,
    ),
    default="INFO",
)
def supervisor(name, window, wakeup, log_level):
    logging.getLogger().setLevel(logging.__dict__[log_level])
    run_supervisor(name, window, wakeup)


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
cli.add_command(debug)

if __name__ == "__main__":
    cli()
