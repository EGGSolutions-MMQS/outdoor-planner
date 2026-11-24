from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Regexp

from ..models import ROLE_ORGANIZER, ROLE_PARTICIPANT


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=40),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Solo lettere, numeri, _ . -"),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    role = SelectField(
        "Ruolo",
        choices=[(ROLE_PARTICIPANT, "Partecipante"), (ROLE_ORGANIZER, "Organizzatore")],
    )


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
