import datetime
import json
from smart_getenv import getenv

from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import InlineFormAdmin
from flask_login import current_user

from kirby.models import ConfigKey, NotificationEmail
from kirby.api.log import LogReader, CORRESPONDENCES_VALUES_LEVELS
from kirby.api.context import EnvironmentVariableAbsence

import logging

admin_logger = logging.getLogger(__name__)


def is_authenticated(user):
    return user.is_authenticated and user.is_active and not user.is_anonymous


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return is_authenticated(current_user)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("security.login", next=request.url))


class UserView(AuthenticatedModelView):
    form_excluded_columns = ("password", "provider")
    column_exclude_list = ("password",)

    def on_form_prefill(self, form, id):
        form.username.render_kw = {"readonly": True}


class ConfigKeyView(AuthenticatedModelView):
    form_excluded_columns = ("job", "context", "scope")
    column_list = ("job_name", "environment_name", "scope", "name", "value")
    column_searchable_list = (
        "scope",
        "name",
        "job.name",
        "context.job.name",
        "context.environment.name",
    )

    def on_form_prefill(self, form, id):
        form.name.render_kw = {"readonly": True}


class ContextConfigKeyInlineModel(InlineFormAdmin):
    form_excluded_columns = ("job", "scope")


class ContextView(AuthenticatedModelView):
    inline_models = [ContextConfigKeyInlineModel(ConfigKey)]


class JobConfigKeyInlineModel(InlineFormAdmin):
    form_excluded_columns = ("context", "scope")


class JobView(AuthenticatedModelView):
    inline_models = [JobConfigKeyInlineModel(ConfigKey)]


class NotificationGroupView(AuthenticatedModelView):
    form_excluded_columns = ("notifications",)
    inline_models = [InlineFormAdmin(NotificationEmail)]


class ScriptView(AuthenticatedModelView):
    form_excluded_columns = (
        "sources",
        "destinations",
        "first_seen",
        "last_seen",
    )


class KirbyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        return super().index()


from ..models import (
    db,
    Environment,
    Job,
    Schedule,
    Context,
    ConfigKey,
    Suspension,
    NotificationGroup,
    Notification,
    Script,
    Topic,
)
from ..models.security import User

admin = Admin(
    name="Kirby",
    url="/admin",
    template_mode="bootstrap3",
    base_template="kirby_master.html",
    index_view=KirbyAdminIndexView(url="/admin"),
)

models = {
    "Scheduling": [Schedule, Suspension],
    "Notifications": [Notification],
    "Jobs": [Environment],
    "Documentation": [Topic],
}


for category, models in models.items():
    for model in models:
        admin.add_view(
            AuthenticatedModelView(model, db.session, category=category)
        )


admin.add_view(UserView(User, db.session, category="Users"))
admin.add_view(
    ConfigKeyView(ConfigKey, db.session, category="Jobs", name="Configuration")
)
admin.add_view(ContextView(Context, db.session, category="Jobs"))
admin.add_view(JobView(Job, db.session, category="Jobs"))
admin.add_view(
    NotificationGroupView(
        NotificationGroup, db.session, category="Notifications"
    )
)
admin.add_view(ScriptView(Script, db.session, category="Jobs"))


class LogView(BaseView):
    def __init__(self, *args, **kargs):
        self.log_reader = LogReader(
            use_tls=getenv("KAFKA_USE_TLS", type=bool, default=True)
        )
        self.rollback_earlier_timestamp = datetime.datetime.utcnow()
        self.delta_datetime = datetime.timedelta(minutes=1)
        super().__init__(*args, **kargs)

    @staticmethod
    def parse_raw_logs(raw_logs):
        return json.dumps(
            {
                "logs": [
                    {
                        "message": log.value,
                        "timestamp": datetime.datetime.fromtimestamp(
                            log.timestamp / 1000
                        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                        "package_name": log.headers["package_name"],
                        "level": log.headers["level"],
                        "value": CORRESPONDENCES_VALUES_LEVELS[
                            log.headers["level"]
                        ],
                    }
                    for log in raw_logs
                ]
            }
        )

    @expose("/")
    def index(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        return self.render("logs/index.html")

    @expose("/new_logs")
    def new_logs(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        else:
            return self.parse_raw_logs(self.log_reader.nexts())

    @expose("/old_logs")
    def old_logs(self):
        earlier = self.rollback_earlier_timestamp
        earliest = self.rollback_earlier_timestamp - self.delta_datetime
        raw_old_logs = self.log_reader.between(
            earliest, earlier, timeout_ms=3000
        )
        parsed_old_logs = self.parse_raw_logs(raw_old_logs)
        self.rollback_earlier_timestamp = earliest
        return parsed_old_logs

    @expose("/script_list")
    def topic_list(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        script_names = [
            script.package_name for script in db.session.query(Script).all()
        ]
        return json.dumps(script_names)


try:
    admin.add_view(LogView(name="Logs", url="/admin/log"))
except EnvironmentVariableAbsence as e:
    admin_logger.error(
        "The Log view isn't initialized because of the following error:"
    )
    admin_logger.error(e)
