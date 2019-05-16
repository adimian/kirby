from datetime import datetime
import copy
import sqlalchemy
from flask import abort
from flask_restplus import Api, Resource, fields
from ..models import db, Job

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
            # To generate all the jobs = since curently package_name and
            # package_version are in the Context data.
            for context in job.contexts:
                jobs.append(
                    {
                        "name": job_name,
                        "package_name": context.package_name,
                        "package_version": context.package_version,
                        "notifications": copy.deepcopy(notifications),
                    }
                )

        return schedule
