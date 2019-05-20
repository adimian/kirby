from datetime import datetime
from cronex import CronExpression
import copy
from flask_restplus import Api, Resource, fields

from ..models import db, Job, JobType

api = Api()

group_model = api.model(
    "Group", {"name": fields.String, "emails": fields.List(fields.String)}
)

notifications_model = api.model(
    "Notifications",
    {
        "on_retry": fields.Boolean,
        "on_failure": fields.Boolean,
        "groups": fields.List(fields.Nested(group_model)),
    },
)

job_model = api.model(
    "Job",
    {
        "name": fields.String,
        "package_name": fields.String,
        "package_version": fields.String,
        "notifications": fields.List(fields.Nested(notifications_model)),
    },
)

schedule_model = api.model(
    "Schedule",
    {
        "date": fields.String(default=str(datetime.utcnow())),
        "jobs": fields.List(fields.Nested(job_model)),
    },
)


def test_schedule(schedule, date):
    cron = CronExpression(
        " ".join(
            [
                schedule.minute or "*",
                schedule.hour or "*",
                schedule.day or "*",
                schedule.month or "*",
                schedule.weekday or "*",
            ]
        )
    )
    now = [date.year, date.month, date.day, date.hour, date.minute]
    return cron.check_trigger(now)


@api.route("/schedule")
class Schedule(Resource):
    @api.marshal_with(schedule_model)
    def get(self):
        date = datetime.utcnow()
        jobs = []
        schedule = {"date": date, "jobs": jobs}

        for job in db.session.query(Job).all():
            job_name = job.name

            # Get Notifications data
            notifications = []
            for notification in job.notifications:
                on_retry = notification.on_retry
                on_failure = notification.on_failure
                groups = [
                    {
                        "name": group.name,
                        "emails": [
                            group_email.email for group_email in group.emails
                        ],
                    }
                    for group in notification.groups
                ]
                notifications.append(
                    {
                        "on_retry": on_retry,
                        "on_failure": on_failure,
                        "groups": copy.deepcopy(groups),
                    }
                )

            # Each Job can have various contexts. We need to go through them
            # To generate all the jobs, since curently package_name and
            # package_version are in the Context data.
            for context in job.contexts:
                if job.type == JobType.TRIGGERED or (
                    context.schedules
                    and any(
                        [
                            test_schedule(schedule, date)
                            for schedule in context.schedules
                        ]
                    )
                ):
                    jobs.append(
                        {
                            "name": job_name,
                            "package_name": context.package_name,
                            "package_version": context.package_version,
                            "notifications": copy.deepcopy(notifications),
                        }
                    )

        return schedule
