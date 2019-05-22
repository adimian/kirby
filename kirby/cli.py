from getpass import getpass

import click
from redis import Redis

from kirby.demo import create_demo_db
from kirby.models import db
from kirby.models.security import user_datastore
from kirby.supervisor.election import Election
from kirby.web import app_maker


@click.command()
@click.option(
    "--host", type=str, default="127.0.0.1", help="The interface to bind to"
)
@click.option("--port", type=str, default="5000", help="The port to bind to")
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

        if click.confirm("Give admin rights?"):
            role = user_datastore.find_role("admin")
            user_datastore.add_role_to_user(user=user, role=role)

        db.session.commit()


@click.command()
@click.argument("name")
@click.option(
    "--window",
    type=int,
    default=5,
    help="Leader election window size (in seconds)",
)
def supervisor(name, window):
    server = Redis()
    with Election(identity=name, server=server, check_ttl=window) as me:
        if me.is_leader():
            print("I'm the leader!")
        else:
            print("I'm NOT the leader :(")


@click.command()
def demo():
    app = app_maker()

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_demo_db(db.session)


@click.group()
def cli():
    pass


cli.add_command(web)
cli.add_command(adduser)
cli.add_command(demo)

if __name__ == "__main__":
    cli()
