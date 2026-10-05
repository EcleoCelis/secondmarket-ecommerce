from flask import Blueprint, g

from backend.app import create_app
from backend.app.auth.decorators import login_required, roles_required
from backend.app.core.config import TestingConfig
from backend.app.core.responses import success_response
from backend.app.extensions import db
from backend.app.models import AuthSession


def create_app_with_protected_routes():
    app = create_app(TestingConfig)
    protected_bp = Blueprint("protected_test", __name__)

    @protected_bp.get("/test/protected")
    @login_required
    def protected_route():
        return success_response({"email": g.current_user.email})

    @protected_bp.get("/test/admin")
    @roles_required("admin")
    def admin_route():
        return success_response({"role": g.current_user.role})

    app.register_blueprint(protected_bp)

    with app.app_context():
        db.create_all()

    return app


def teardown_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register_buyer(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "Secondhand2026",
            "first_name": "Second",
            "last_name": "Buyer",
            "role": "buyer",
        },
    )


def test_login_required_rejects_anonymous_requests():
    app = create_app_with_protected_routes()

    response = app.test_client().get("/test/protected")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "authentication_required"
    teardown_app(app)


def test_login_required_allows_authenticated_user():
    app = create_app_with_protected_routes()
    client = app.test_client()

    register_buyer(client)
    response = client.get("/test/protected")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["email"] == "buyer@example.com"
    teardown_app(app)


def test_roles_required_rejects_wrong_role():
    app = create_app_with_protected_routes()
    client = app.test_client()

    register_buyer(client)
    response = client.get("/test/admin")
    payload = response.get_json()

    assert response.status_code == 403
    assert payload["error"]["code"] == "permission_denied"
    assert payload["error"]["details"]["required_roles"] == ["admin"]
    teardown_app(app)


def test_revoked_session_cannot_access_protected_route():
    app = create_app_with_protected_routes()
    client = app.test_client()

    register_buyer(client)
    with app.app_context():
        session = AuthSession.query.one()
        session.revoke()
        db.session.commit()

    response = client.get("/test/protected")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "authentication_required"
    teardown_app(app)
