from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class OutingForm(FlaskForm):
    title = StringField("Titolo", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Descrizione", validators=[Length(max=5000)])
    location_query = StringField("Luogo (cerca per nome)", validators=[Length(max=100)])
    search = SubmitField("Cerca luogo")
    location_choice = SelectField(
        "Risultati", choices=[], validate_choice=False, validators=[Optional()]
    )
    starts_at = DateTimeLocalField(
        "Data e ora", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    max_seats = IntegerField("Posti massimi", validators=[DataRequired(), NumberRange(1, 500)])
    gpx = FileField(
        "Traccia GPX (opzionale, max 2 MB)",
        validators=[Optional(), FileAllowed(["gpx"], "Solo file .gpx")],
    )
    remove_gpx = BooleanField("Rimuovi la traccia attuale")
    save = SubmitField("Salva")
