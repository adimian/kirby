from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import abort
from cronex import CronExpression
import copy
from flask_restplus import Api, Resource, reqparse, fields

from ..models import db, Script, Topic, Job, JobType

api = Api()

registration_parser = reqparse.RequestParser()
registration_parser.add_argument("script_id", type=int)
registration_parser.add_argument(
    "source_id", type=int, action="append", default=[]
)
registration_parser.add_argument(
    "destination_id", type=int, action="append", default=[]
)


@api.route("/registration")
class Registration(Resource):
    @api.expect(registration_parser)
    def patch(self):
        args = registration_parser.parse_args()

        # Update last_seen
        try:
            script = (
                db.session.query(Script).filter_by(id=args["script_id"]).one()
            )
            script.last_seen = datetime.utcnow()
        except NoResultFound:
            abort(
                400,
                f"The script with the 'id':{args['script_id']}, doesn't exist.",
            )

        # Add sources and destinations
        for source_id in args["source_id"]:
            try:
                source = db.session.query(Topic).filter_by(id=source_id).one()
                script.add_source(source)
            except NoResultFound:
                db.session.rollback()
                abort(
                    400,
                    f"The topic with the 'id':{source_id}, doesn't exist. "
                    f"No changes has been committed.",
                )
        for destination_id in args["destination_id"]:
            try:
                destination = (
                    db.session.query(Topic).filter_by(id=destination_id).one()
                )
                script.add_destination(destination)
            except NoResultFound:
                db.session.rollback()
                abort(
                    400,
                    f"The topic with the 'id':{destination_id}, doesn't exist. "
                    f"No changes has been committed.",
                )

        db.session.commit()

        return {"message": "Sucess"}


topic_parser = reqparse.RequestParser()
topic_parser.add_argument("name", type=str, required=True)


@api.route("/topic")
class TopicView(Resource):
    @api.expect(topic_parser)
    def get(self):
        args = topic_parser.parse_args()
        topic = db.session.query(Topic).filter_by(name=args["name"]).one()
        return {"id": topic.id, "name": topic.name}


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

config_model = api.model(
    "Config", {"key": fields.String, "value": fields.String}
)


job_model = api.model(
    "Job",
    {
        "name": fields.String,
        "environment": fields.String,
        "package_name": fields.String,
        "package_version": fields.String,
        "notifications": fields.List(fields.Nested(notifications_model)),
        "variables": fields.List(fields.Nested(config_model)),
    },
)

schedule_model = api.model(
    "Schedule",
    {
        "date": fields.String(default=str(datetime.utcnow())),
        "jobs": fields.List(fields.Nested(job_model)),
    },
)


def should_run(schedule, date):
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
            # to generate all the jobs. And for each context, linked scripts
            # contains the package_name and package_version are in the Context
            # data.
            for context in job.contexts:
                if job.type == JobType.TRIGGERED or (
                    context.schedules
                    and any(
                        [
                            should_run(schedule, date)
                            for schedule in context.schedules
                        ]
                    )
                ):
                    for script in context.scripts:
                        jobs.append(
                            {
                                "name": job_name,
                                "environment": context.environment.name,
                                "package_name": script.package_name,
                                "package_version": script.package_version,
                                "notifications": copy.deepcopy(notifications),
                                "variables": [
                                    {"key": k, "value": v}
                                    for k, v in context.variables().items()
                                ],
                            }
                        )

        return schedule
