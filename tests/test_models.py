from kirby.models import (
    Job,
    Environment,
    JobType,
    Context,
    Schedule,
    Suspension,
    NotificationGroup,
)


def test_it_creates_a_job():

    job = Job(
        name="retrieve cash register data",
        description="connects to the cash register API and fetches latest sale",
        type=JobType.SCHEDULED,
    )

    test_env = Environment(name="test")

    context = Context(environment=test_env, package_name="my_script")
    context.set_config(url="http://localhost:8000", loop=30, retry=True)

    schedule = Schedule(hour="*", minute="/2")
    context.add_schedule(schedule)

    suspension = Suspension(start="2019-01-01", end="2019-01-02")
    schedule.add_suspension(suspension)

    group = NotificationGroup()
    group.add_email("admin@local.local")

    job.add_context(context)
    job.add_notification(group, on_retry=True, on_failure=True)
