import datetime
import dateutil.parser
import json
from smart_getenv import getenv
from timeloop import Timeloop

from flask import redirect, url_for, request, abort
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import InlineFormAdmin
from flask_login import current_user

from kirby.models import ConfigKey, NotificationEmail
from kirby.api.log import LogReader, CORRESPONDENCES_VALUES_LEVELS
from kirby.api.context import MissingEnvironmentVariable

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

    cookie_name_session_id = "log_session"
    session_expiration = datetime.timedelta(seconds=10)
    tl = Timeloop()

    def __init__(self, *args, **kargs):
        self.sessions = {}
        self.rollback_earlier_timestamp = datetime.datetime.utcnow()
        self.delta_datetime = datetime.timedelta(minutes=1)
        super().__init__(*args, **kargs)
        LogView.tl._add_job(
            func=self.clean_sessions, interval=LogView.session_expiration
        )
        LogView.tl.start()

    def clean_sessions(self):
        session_names = list(self.sessions.keys())
        for session_name in session_names:
            session = self.sessions[session_name]
            if (
                session["last_seen"] + self.session_expiration
                < datetime.datetime.utcnow()
            ):
                admin_logger.info(
                    f"Cleaning session='{session_name}' after "
                    f"{self.session_expiration.total_seconds()} seconds "
                    "of inactivity"
                )
                session["log_reader"].close()
                self.sessions.pop(session_name)

    def get_session_id(self):
        session_id = request.cookies[self.cookie_name_session_id]
        return session_id

    def get_log_reader(self):
        session_id = self.get_session_id()
        if session_id in self.sessions.keys():
            session = self.sessions[session_id]
            session["last_seen"] = datetime.datetime.utcnow()
            return session["log_reader"]
        else:
            abort(
                401,
                f"You haven't started your session. "
                "Please use the endpoint /admin/log/start_session",
            )

    @staticmethod
    def parse_raw_logs(raw_logs):
        if raw_logs:
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
        else:
            return json.dumps({"logs": []})

    @expose("/")
    def index(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        return self.render("logs/index.html")

    @expose("/start_session", methods=("POST",))
    def start_session(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        else:
            session_id = self.get_session_id()
            self.sessions[session_id] = {
                "log_reader": LogReader(
                    use_tls=getenv(
                        "KAFKA_USE_TLS",
                        type=bool,
                        default=True,
                        group_id=session_id,
                    )
                ),
                "last_seen": datetime.datetime.utcnow(),
            }
        return json.dumps(
            {"status_code": 200, "message": "The session has been started."}
        )

    @expose("/new_logs")
    def new_logs(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        else:
            return self.parse_raw_logs(self.get_log_reader().nexts())

    @expose("/old_logs")
    def old_logs(self):
        if not is_authenticated(current_user):
            return redirect(url_for("security.login", next=request.url))
        else:
            try:
                start_datetime = dateutil.parser.parse(
                    request.args.get("start")
                )
                end_datetime = dateutil.parser.parse(request.args.get("end"))
            except (ValueError, TypeError) as e:
                abort(
                    400, f"The format of the given date is not correct : {e}"
                )
            else:
                raw_old_logs = self.get_log_reader().between(
                    start_datetime, end_datetime, timeout_ms=3000
                )
                parsed_old_logs = self.parse_raw_logs(raw_old_logs)
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
except MissingEnvironmentVariable as e:
    admin_logger.error(
        "The Log view isn't initialized because of the following error:"
    )
    admin_logger.error(e)
