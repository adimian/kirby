import click
import logging
import os
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
def database(file):
    app = app_maker()
    db.init_app(app)

    tables = db.metadata.tables
    if tables:
        if click.confirm("Do you want to drop all the existing tables in db?"):
            with app.app_context():
                db.drop_all()
        else:
            click.echo("No modification have been applied")
            return

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        create_example_db(db.session, file)

    click.echo("Data for example project inserted in the database")


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
    for package in os.scandir(os.path.join(file_path, "scripts")):
        if package.is_dir():
            logging.info(f"Build and upload {package}")
            build_and_upload(package, repo)


@click.command()
@click.option(
    "--script_name",
    type=str,
    help="Name of the script that will be created",
    prompt=True,
)
@click.option(
    "--author_name",
    type=str,
    help="Name of the author of the script",
    default="Kirby Team",
    prompt=True,
)
def create(script_name, author_name):
    path = os.path.dirname(os.path.abspath(__file__))

    package_dir = os.path.join(path, "scripts", script_name)
    os.mkdir(package_dir)

    package_code_dir = os.path.join(package_dir, script_name)
    os.mkdir(package_code_dir)
    with open(
        os.path.join(package_code_dir, "__main__.py"), "w+"
    ) as main_file:
        main_file.write(
            """if __name__ == "__main__":
    pass
"""
        )
    with open(os.path.join(package_dir, "setup.py"), "w+") as setup_file:
        setup_file.write(
            f"""from distutils.core import setup

setup(
    name="{script_name}",
    version="0.0.1",
    author="{author_name}",
    license="MIT",
    packages=["{script_name}"],
)
"""
        )


packages.add_command(upload)
packages.add_command(create)


@click.group()
def cli():
    pass


cli.add_command(database)
cli.add_command(packages)

if __name__ == "__main__":
    cli()
