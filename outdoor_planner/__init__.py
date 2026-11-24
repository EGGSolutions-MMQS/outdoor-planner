import os

from flask import Flask

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not set: define it in the environment or in .env")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Accedi per continuare."

    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .outings.routes import bp as outings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(outings_bp)

    with app.app_context():
        from . import models

        db.create_all()

    return app
