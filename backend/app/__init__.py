from flask import Flask, abort, send_from_directory

from backend.app.api import api_bp
from backend.app.cli import register_cli_commands
from backend.app.core.config import get_config
from backend.app.core.errors import register_error_handlers
from backend.app.extensions import db, migrate


def create_app(config_object=None):
    app = Flask(
        __name__,
        static_folder="../../frontend/static",
        static_url_path="/static",
    )
    app.config.from_object(config_object or get_config())

    db.init_app(app)
    migrate.init_app(app, db)
    import backend.app.models  # noqa: F401

    register_cli_commands(app)
    register_error_handlers(app)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.get("/")
    def storefront():
        return send_from_directory(app.config["FRONTEND_ROOT"], "index.html")

    @app.get("/admin")
    @app.get("/admin/")
    def admin_frontend():
        return send_from_directory(app.config["FRONTEND_ROOT"], "admin/index.html")

    @app.get("/checkout")
    @app.get("/checkout/")
    def checkout_frontend():
        return send_from_directory(app.config["FRONTEND_ROOT"], "checkout/index.html")

    @app.get("/orders")
    @app.get("/orders/")
    def orders_frontend():
        return send_from_directory(app.config["FRONTEND_ROOT"], "orders/index.html")

    @app.get("/<path:path>")
    def frontend_fallback(path):
        if path.startswith("api/"):
            abort(404)
        if "." in path:
            return send_from_directory(app.config["FRONTEND_ROOT"], path)
        return send_from_directory(app.config["FRONTEND_ROOT"], "index.html")

    return app
