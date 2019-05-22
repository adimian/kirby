from enum import Enum


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.orm import Session

db = SQLAlchemy()


class Environment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)

    def __repr__(self):
        return f"<Environment name={self.name}>"


class JobType(Enum):
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    description = db.Column(db.Text())
    type = db.Column(db.Enum(JobType), nullable=False)

    def add_context(self, context):
        self.contexts.append(context)

    def add_notification(self, group, on_retry=False, on_failure=True):
        notification = Notification(on_retry=on_retry, on_failure=on_failure)
        notification.groups.append(group)
        self.notifications.append(notification)

    def set_config(self, **kwargs):
        for key, value in kwargs.items():
            c = ConfigKey(name=key, value=str(value))
            self.configkeys.append(c)

    def __repr__(self):
        return f"<Job name={self.name} type={self.type.value}>"


schedules_to_contexts = db.Table(
    "schedules_to_contexts",
    db.metadata,
    db.Column("schedule", db.Integer, db.ForeignKey("schedule.id")),
    db.Column("context", db.Integer, db.ForeignKey("context.id")),
)


class Context(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    environment_id = db.Column(
        db.Integer, db.ForeignKey("environment.id"), nullable=False
    )
    environment = db.relationship(
        Environment, backref=db.backref("contexts", lazy=True)
    )

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    job = db.relationship(Job, backref=db.backref("contexts", lazy=True))

    schedules = db.relationship(
        "Schedule", secondary=schedules_to_contexts, back_populates="contexts"
    )

    def set_config(self, **kwargs):
        for key, value in kwargs.items():
            c = ConfigKey(name=key, value=str(value))
            self.configkeys.append(c)

    def add_schedule(self, schedule):
        self.schedules.append(schedule)

    def __repr__(self):
        return f"<Context job={self.job} environment={self.environment}>"


class ConfigScope(Enum):
    GLOBAL = "global"
    JOB = "job"
    CONTEXT = "context"


class ConfigKey(db.Model):
    __table_args__ = (
        UniqueConstraint(
            "name", "context_id", "job_id", name="_context_name_uc"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    value = db.Column(db.String(), nullable=False)
    scope = db.Column(db.Enum(ConfigScope), nullable=False)

    context_id = db.Column(
        db.Integer, db.ForeignKey("context.id"), nullable=True
    )
    context = db.relationship(
        Context, backref=db.backref("configkeys", lazy=True)
    )

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=True)
    job = db.relationship(Job, backref=db.backref("configkeys", lazy=True))

    @property
    def job_name(self):
        if self.job:
            return self.job.name
        elif self.context:
            return self.context.job.name

    @property
    def environment_name(self):
        if self.context:
            return self.context.environment.name


@event.listens_for(Session, "before_flush")
def set_config_scope(session, flush_context, instances):
    for target in set(session.new).union(set(session.dirty)):
        if isinstance(target, ConfigKey):
            if target.context or target.context_id:
                target.scope = ConfigScope.CONTEXT
            elif target.job or target.job_id:
                target.scope = ConfigScope.JOB
            else:
                target.scope = ConfigScope.GLOBAL


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    hour = db.Column(db.String(), default="*")
    minute = db.Column(db.String(), default="*")
    day = db.Column(db.String(), default="*")
    month = db.Column(db.String(), default="*")
    weekday = db.Column(db.String(), default="*")

    contexts = db.relationship(
        "Context", secondary=schedules_to_contexts, back_populates="schedules"
    )

    def add_suspension(self, suspension):
        self.suspensions.append(suspension)


class Suspension(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text(), nullable=True)

    schedule_id = db.Column(
        db.Integer, db.ForeignKey("schedule.id"), nullable=False
    )
    schedule = db.relationship(
        Schedule, backref=db.backref("suspensions", lazy=True)
    )


notification_to_groups = db.Table(
    "notification_to_groups",
    db.metadata,
    db.Column("notification", db.Integer, db.ForeignKey("notification.id")),
    db.Column(
        "notification_group",
        db.Integer,
        db.ForeignKey("notification_group.id"),
    ),
)


class NotificationGroup(db.Model):
    __tablename__ = "notification_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)

    notifications = db.relationship(
        "Notification",
        secondary=notification_to_groups,
        back_populates="groups",
    )

    def add_email(self, email):
        ne = NotificationEmail(email=email)
        self.emails.append(ne)


class NotificationEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), nullable=False)

    notification_group_id = db.Column(
        db.Integer, db.ForeignKey("notification_group.id"), nullable=False
    )
    notification_group = db.relationship(
        NotificationGroup, backref=db.backref("emails", lazy=True)
    )


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    on_retry = db.Column(db.Boolean, nullable=False, default=False)
    on_failure = db.Column(db.Boolean, nullable=False, default=True)

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    job = db.relationship(Job, backref=db.backref("notifications", lazy=True))

    groups = db.relationship(
        "NotificationGroup",
        secondary=notification_to_groups,
        back_populates="notifications",
    )


class Script(db.Model):
    __tablename__ = "script"
    id = db.Column(db.Integer, primary_key=True)
    package_name = db.Column(db.String(), nullable=False)
    package_version = db.Column(db.String(), nullable=False)

    context_id = db.Column(
        db.Integer, db.ForeignKey("context.id"), nullable=False
    )
    context = db.relationship(
        Context, backref=db.backref("scripts", lazy=True)
    )

    first_seen = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)

    def add_source(self, source):
        self.sources.append(source)

    def add_destination(self, destination):
        self.destinations.append(destination)

    def __repr__(self):
        return f"<Script name={self.package_name} package_version={self.package_version}>"


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)

    subscriber_id = db.Column(db.Integer, db.ForeignKey("script.id"))
    subscriber = db.relationship(
        Script,
        backref=db.backref("sources", lazy=True),
        foreign_keys=[subscriber_id],
    )

    provider_id = db.Column(db.Integer, db.ForeignKey("script.id"))
    provider = db.relationship(
        Script,
        backref=db.backref("destinations", lazy=True),
        foreign_keys=[provider_id],
    )

    def __repr__(self):
        return f"<Topic name={self.name}>"
