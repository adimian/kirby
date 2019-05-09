import sqlalchemy
from flask import abort
from flask_restplus import Api, Resource, fields, reqparse
from ..models import db, Job, JobType

api = Api()

client_model = api.model(
    "Client", {"id": fields.Integer, "name": fields.String}
)

registration_parser = reqparse.RequestParser()
registration_parser.add_argument("name", type=str, required=True)
registration_parser.add_argument("description", type=str)
registration_parser.add_argument(
    "type", choices=["scheduled", "triggered"], required=True
)


@api.route("/registration")
class Registration(Resource):
    @api.expect(registration_parser)
    def post(self):
        args = registration_parser.parse_args()
        try:
            db.session.add(
                Job(
                    name=args["name"],
                    description=args.get("description"),
                    type=JobType(args["type"]),
                )
            )
            db.session.commit()
            return {
                "id": db.session.query(Job)
                .filter_by(name=args["name"])
                .first()
                .id
            }
        except sqlalchemy.exc.IntegrityError:
            abort(400, "Bad request")
