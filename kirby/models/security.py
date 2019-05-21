from flask_security import SQLAlchemyUserDatastore, Security
from flask_security import RoleMixin, UserMixin

from . import db


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), default=True)
    provider = db.Column(db.String(100), default="local")
    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )

    @property
    def is_local(self):
        return self.provider == "local"

    @property
    def is_admin(self):
        return self.has_role("admin")


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()
