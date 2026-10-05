from flask import Blueprint, current_app

from backend.app.core.responses import success_response


system_bp = Blueprint("system", __name__)


@system_bp.get("/info")
def system_info():
    return success_response(
        {
            "app": current_app.config["APP_NAME"],
            "version": current_app.config["APP_VERSION"],
            "environment": current_app.config["ENV_NAME"],
            "api_version": "v1",
            "roles": ["buyer", "admin"],
            "modules": {
                "current": "01-system-foundation",
                "next": "02-database-core-domain-models",
            },
        }
    )
