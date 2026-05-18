from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from backend.config import Config
from backend.extensions import db, migrate
from backend.routes import register_blueprints
from backend.seed import seed_database


def create_app():
    load_dotenv()
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path="",
    )
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    with app.app_context():
        from backend import models  # noqa: F401

        db.create_all()
        seed_database()

    return app
