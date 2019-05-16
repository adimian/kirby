from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from flask import abort
from datetime import datetime
from flask_restplus import Api, Resource, reqparse
from ..models import db, Script, Topic

api = Api()

registration_parser = reqparse.RequestParser()
registration_parser.add_argument("script_id", type=int)
registration_parser.add_argument("source_id", type=int, action="append")
registration_parser.add_argument("destination_id", type=int, action="append")


@api.route("/registration")
class Registration(Resource):
    @api.expect(registration_parser)
    def patch(self):
        args = registration_parser.parse_args()

        try:
            # Update last_seen
            script = (
                db.session.query(Script).filter_by(id=args["script_id"]).one()
            )
            script.last_seen = datetime.utcnow()

            # Add sources and destinations
            for source_id in args["source_id"]:
                source = db.session.query(Topic).filter_by(id=source_id).one()
                script.add_source(source)
            for destination_id in args["destination_id"]:
                destination = (
                    db.session.query(Topic).filter_by(id=destination_id).one()
                )
                script.add_destination(destination)

            db.session.commit()

            return {"message": "Sucess"}
        except NoResultFound:
            abort(
                400,
                "One or many of the given 'id' refer to inexistent objects.",
            )


topic_parser = reqparse.RequestParser()
topic_parser.add_argument("name", type=str, required=True)


@api.route("/topic")
class TopicView(Resource):
    @api.expect(topic_parser)
    def get(self):
        args = topic_parser.parse_args()
        topic = db.session.query(Topic).filter_by(name=args["name"]).one()
        return {"id": topic.id, "name": topic.name}
