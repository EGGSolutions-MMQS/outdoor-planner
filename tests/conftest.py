from datetime import datetime, timedelta
from pathlib import Path

import pytest

from outdoor_planner import create_app
from outdoor_planner.config import TestConfig
from outdoor_planner.extensions import db
from outdoor_planner.models import Outing, User

FIXTURES = Path(__file__).parent / "fixtures"
TEST_PASSWORD = "test-pass-123"


@pytest.fixture
def app(tmp_path):
    class Config(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    app = create_app(Config)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(username, role):
        with app.app_context():
            user = User(username=username, role=role)
            user.set_password(TEST_PASSWORD)
            db.session.add(user)
            db.session.commit()
            return user.id

    return _make


@pytest.fixture
def make_outing(app):
    def _make(organizer_id, days=30, seats=5, title="Gita di prova"):
        with app.app_context():
            outing = Outing(
                title=title,
                description="Descrizione",
                location_name="Bergamo, Lombardia, Italia",
                latitude=45.69,
                longitude=9.67,
                starts_at=datetime.now() + timedelta(days=days),
                max_seats=seats,
                organizer_id=organizer_id,
            )
            db.session.add(outing)
            db.session.commit()
            return outing.id

    return _make


@pytest.fixture
def login(client):
    def _login(username):
        client.post("/logout")
        return client.post("/login", data={"username": username, "password": TEST_PASSWORD})

    return _login
