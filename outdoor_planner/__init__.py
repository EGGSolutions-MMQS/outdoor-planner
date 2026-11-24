import os

from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is not set: define it in the environment or in .env")

    app.config["UPLOAD_FOLDER"] = os.path.abspath(app.config["UPLOAD_FOLDER"])
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
        db.create_all()

    register_error_handlers(app)
    return app


def register_error_handlers(app):
    messages = {
        403: "Non hai i permessi per questa azione.",
        404: "Pagina non trovata.",
        413: "File troppo grande (massimo 2 MB).",
    }

    def handle(error):
        return render_template("errors/error.html", code=error.code, message=messages[error.code]), error.code

    for code in messages:
        app.register_error_handler(code, handle)
