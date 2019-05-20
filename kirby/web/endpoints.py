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
                    f"The topic with the 'id':{source_id}, doesn't exist. No changes has been committed.",
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
                    f"The topic with the 'id':{destination_id}, doesn't exist. No changes has been committed.",
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
