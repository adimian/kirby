import click
import os

from dotenv import load_dotenv

from .populate_database import create_example_db
from kirby.models import db
from kirby.web import app_maker

load_dotenv()


@click.command()
@click.option(
    "--json_file_path",
    type=str,
    default=os.path.join(os.path.dirname(__file__), "demo.json"),
    help="demo json path file",
)
def database(json_file_path):
    app = app_maker()

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_example_db(db.session, json_file_path)

    click.echo("demo data inserted in the database")


@click.group()
def package():
    pass


@click.command()
def create():
    pass


@click.command()
def install():
    pass


package.add_command(create)
package.add_command(install)


@click.group()
def cli():
    pass


cli.add_command(database)
cli.add_command(package)

if __name__ == "__main__":
    cli()
