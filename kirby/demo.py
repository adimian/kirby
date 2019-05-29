from os import name

from kirby.models import ConfigKey
from kirby.models.security import user_datastore
from kirby import models


def create_demo_db(s):

    # create demo user
    user = user_datastore.create_user(username="demo", password="demo")
    role = user_datastore.find_role("admin")
    user_datastore.add_role_to_user(user=user, role=role)
    s.commit()

    sysadmins = models.NotificationGroup(name="sysadmins")
    sysadmins.add_email("alice@local.local")
    sysadmins.add_email("bob@local.local")
    sysadmins.add_email("charles@local.local")

    s.add(sysadmins)
    s.commit()

    # fill the database with dummy content
    job = models.Job(
        name="Fetch bakery realtime sales", type=models.JobType.SCHEDULED
    )
    s.add(job)
    job.add_notification(sysadmins, on_failure=True, on_retry=False)

    job.set_config(
        SENTRY_DSN="http://sentry.dsn.somewhere", SSH_USERNAME="demo"
    )

    dev = models.Environment(name="Development")
    test = models.Environment(name="Test")
    prod = models.Environment(name="Production")

    s.add_all([dev, test, prod])

    dev_ctx = models.Context(job=job, environment=dev)
    dev_ctx.set_config(ENV="dev", SSH_SERVER="dev.server.somewhere:22")
    test_ctx = models.Context(job=job, environment=test)
    test_ctx.set_config(ENV="test", SSH_SERVER="test.server.somewhere:25")
    prod_ctx = models.Context(job=job, environment=prod)
    prod_ctx.set_config(ENV="prod", SSH_SERVER="server.somewhere:22")
    s.add_all([dev_ctx, test_ctx, prod_ctx])

    schedule = models.Schedule(
        name="every two minutes", hour="*", minute="*/2"
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

    s.add(ConfigKey(name="KAFKA_URL", value="some.kafka.server:9999"))

    s.commit()
