import sqlalchemy
from flask import abort
from flask_restplus import Api, Resource, fields, reqparse
from ..models import db, Job, JobType

api = Api()

client_model = api.model(
    "Client", {"id": fields.Integer, "name": fields.String}
)


def is_job_type(value):
    if value == JobType.SCHEDULED.value:
        return JobType(JobType.SCHEDULED.value)
    elif value == JobType.TRIGGERED.value:
        return JobType(JobType.SCHEDULED.value)
    else:
        raise ValueError("This is not a valid job type.")


# Swagger documentation
is_job_type.__schema__ = {"type": "string", "format": "scheduled or triggered"}

registration_parser = reqparse.RequestParser()
registration_parser.add_argument("name", type=str, required=True)
registration_parser.add_argument("description", type=str)
registration_parser.add_argument("type", type=is_job_type)


@api.route("/registration")
class ClientList(Resource):
    @api.expect(registration_parser)
    def post(self):
        args = registration_parser.parse_args()
        try:
            db.session.add(
                Job(
                    name=args["name"],
                    description=args["description"],
                    type=args["type"],
                )
            )
            db.session.commit()
            return {
                "id": db.session.query(Job).filter_by(name=args["name"]).first().id
            }
        except sqlalchemy.exc.IntegrityError:
            abort(500, "There is already a client with this name")
