from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager

ROLE_ORGANIZER = "organizer"
ROLE_PARTICIPANT = "participant"


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_organizer(self):
        return self.role == ROLE_ORGANIZER


class Outing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    location_name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    max_seats = db.Column(db.Integer, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    gpx_filename = db.Column(db.String(64))
    gpx_original_name = db.Column(db.String(200))
    gpx_distance_km = db.Column(db.Float)
    gpx_points = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    organizer = db.relationship("User", backref="outings")
    signups = db.relationship("Signup", backref="outing", cascade="all, delete-orphan")
    comments = db.relationship(
        "Comment", backref="outing", cascade="all, delete-orphan", order_by="Comment.created_at"
    )

    @property
    def seats_left(self):
        return self.max_seats - len(self.signups)

    @property
    def is_past(self):
        return self.starts_at < utcnow()


class Signup(db.Model):
    __table_args__ = (db.UniqueConstraint("outing_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    outing_id = db.Column(db.Integer, db.ForeignKey("outing.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    outing_id = db.Column(db.Integer, db.ForeignKey("outing.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    author = db.relationship("User")


class WeatherCache(db.Model):
    __table_args__ = (db.UniqueConstraint("latitude", "longitude", "day"),)

    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    day = db.Column(db.Date, nullable=False)
    payload = db.Column(db.Text, nullable=False)
    fetched_at = db.Column(db.DateTime, default=utcnow, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
