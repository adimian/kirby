import click
import os
import logging
import subprocess

from dotenv import load_dotenv

from .populate_database import create_example_db
from kirby.models import db
from kirby.web import app_maker

load_dotenv()

logging.getLogger("kafka").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-f",
    "--file",
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
def packages():
    pass


def build_and_upload(package_dir, repo):
    p = subprocess.Popen(
        ["python", "setup.py", "sdist", "upload", "-r", repo], cwd=package_dir
    )
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(
            f"Please check the error above, something went wrong during the "
            "upload of the package"
        )


@click.command()
@click.option("--repo", type=str, help="PyPi repository", prompt=True)
def upload(repo):
    file_path = os.path.dirname(os.path.abspath(__file__))
    # packages_ = os.listdir(os.path.join(file_path, "scripts"))
    # for package in packages_:
    for package in os.scandir(os.path.join(file_path, "scripts")):
        if package.is_dir():
            logging.info(f"Build and upload {package}")
            build_and_upload(package, repo)


packages.add_command(upload)


@click.group()
def cli():
    pass


cli.add_command(database)
cli.add_command(packages)

if __name__ == "__main__":
    cli()
