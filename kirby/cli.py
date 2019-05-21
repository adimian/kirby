import click

from getpass import getpass
from kirby.web import app_maker
from kirby.models.security import user_datastore
from kirby.models import db


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


@click.group()
def cli():
    pass


cli.add_command(web)
cli.add_command(adduser)

if __name__ == "__main__":
    cli()
