from flask import current_app, request
from flask_security.confirmable import requires_confirmation
from flask_security.forms import (
    NextFormMixin,
    get_form_field_label,
    config_value,
)
from flask_security.utils import get_message, verify_and_update_password
from flask_wtf import FlaskForm
from werkzeug.local import LocalProxy
from wtforms import BooleanField, PasswordField, StringField, SubmitField


_security = LocalProxy(lambda: current_app.extensions["security"])
_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)

import logging

logger = logging.getLogger(__name__)


class LoginForm(FlaskForm, NextFormMixin):
    """Username login form"""

    username = StringField(get_form_field_label("username"))
    password = PasswordField(get_form_field_label("password"))
    remember = BooleanField(get_form_field_label("remember_me"))
    submit = SubmitField(get_form_field_label("login"))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        if not self.next.data:
            self.next.data = request.args.get("next", "")
        self.remember.default = config_value("DEFAULT_REMEMBER_ME")

    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        if not self.username.data.strip():
            self.username.errors.append("Username not provided")
            return False

        if not self.password.data.strip():
            self.password.errors.append(
                get_message("PASSWORD_NOT_PROVIDED")[0]
            )
            return False

        username = self.username.data
        self.user = _security.datastore.find_user(username=username)
        if not self.user:
            logger.warning(
                "not found {} using username field, "
                "now using fallback with email".format(username)
            )
            self.user = _security.datastore.find_user(email=username)

        if self.user is None:
            self.username.errors.append(get_message("USER_DOES_NOT_EXIST")[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message("PASSWORD_NOT_SET")[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message("INVALID_PASSWORD")[0])
            return False
        if requires_confirmation(self.user):
            self.username.errors.append(
                get_message("CONFIRMATION_REQUIRED")[0]
            )
            return False
        if not self.user.is_active:
            self.username.errors.append(get_message("DISABLED_ACCOUNT")[0])
            return False
        return True
