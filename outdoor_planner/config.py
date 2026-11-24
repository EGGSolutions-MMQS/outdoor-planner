import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///outdoor_planner.db")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB, bounds GPX uploads
    WEATHER_CACHE_HOURS = 3
    FORECAST_MAX_DAYS = 16
    HTTP_TIMEOUT = 5


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-only-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    UPLOAD_FOLDER = "uploads-test"
    WTF_CSRF_ENABLED = False
