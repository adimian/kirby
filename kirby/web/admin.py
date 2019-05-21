from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from ..models import (
    db,
    Environment,
    Job,
    Schedule,
    Context,
    ConfigKey,
    Suspension,
    NotificationEmail,
    NotificationGroup,
    Notification,
    Script,
    Topic,
)
from ..models.security import User

admin = Admin(template_mode="bootstrap3")

models = (
    Job,
    Environment,
    Schedule,
    Context,
    ConfigKey,
    Suspension,
    NotificationEmail,
    NotificationGroup,
    Notification,
    Script,
    Topic,
    User,
)


for model in models:
    admin.add_view(ModelView(model, db.session))
