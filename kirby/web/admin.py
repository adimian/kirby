from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from ..models import (
    db,
    Job,
    Schedule,
    Context,
    ConfigKey,
    Suspension,
    NotificationEmail,
    NotificationGroup,
    Notification,
)

admin = Admin(template_mode="bootstrap3")

models = (
    Job,
    Schedule,
    Context,
    ConfigKey,
    Suspension,
    NotificationEmail,
    NotificationGroup,
    Notification,
)


for model in models:
    admin.add_view(ModelView(model, db.session))
