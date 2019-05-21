import click

from getpass import getpass
from kirby.web import app_maker
from kirby.models.security import user_datastore
from kirby.models import db
from kirby import models


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
def demo():
    app = app_maker()

    with app.app_context():
        app.try_trigger_before_first_request_functions()
        s = db.session

        # create demo user
        user = user_datastore.create_user(username="demo", password="demo")
        role = user_datastore.find_role("admin")
        user_datastore.add_role_to_user(user=user, role=role)
        s.commit()

        # fill the database with dummy content
        job = models.Job(
            name="Fetch bakery realtime sales", type=models.JobType.SCHEDULED
        )
        s.add(job)

        dev = models.Environment(name="Development")
        test = models.Environment(name="Test")
        prod = models.Environment(name="Production")

        s.add_all([dev, test, prod])

        dev_ctx = models.Context(job=job, environment=dev)
        test_ctx = models.Context(job=job, environment=test)
        prod_ctx = models.Context(job=job, environment=prod)
        s.add_all([dev_ctx, test_ctx, prod_ctx])

        schedule = models.Schedule(
            name="every two minutes", hour="*", minute="/2"
        )
        s.add(schedule)
        dev_ctx.add_schedule(schedule)
        test_ctx.add_schedule(schedule)
        prod_ctx.add_schedule(schedule)

        source = models.Topic(name="bakery")
        s.add(source)
        destination = models.Topic(name="timeseries")
        s.add(destination)

        dev_script = models.Script(
            context=dev_ctx,
            package_name="test_package_for_dev",
            package_version="2.0.1",
        )
        dev_script.add_source(source)
        dev_script.add_destination(destination)

        test_script = models.Script(
            context=dev_ctx,
            package_name="test_package_for_test",
            package_version="1.0.1",
        )
        test_script.add_source(source)
        test_script.add_destination(destination)

        prod_script = models.Script(
            context=dev_ctx,
            package_name="test_package_for_prod",
            package_version="0.0.5",
        )
        prod_script.add_source(source)
        prod_script.add_destination(destination)

        s.add_all([dev_script, test_script, prod_script])

        s.commit()


@click.group()
def cli():
    pass


cli.add_command(web)
cli.add_command(adduser)
cli.add_command(demo)

if __name__ == "__main__":
    cli()
