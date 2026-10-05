from backend.app import create_app
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import AuthSession, User


def setup_test_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
    return app


def teardown_test_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_register_rejects_invalid_payload():
    app = setup_test_app()

    response = app.test_client().post("/api/v1/auth/register", json={"email": "bad", "password": "weak"})
    payload = response.get_json()

    assert response.status_code == 422
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"
    assert "email" in payload["error"]["details"]
    assert "password" in payload["error"]["details"]
    assert "first_name" in payload["error"]["details"]
    assert "last_name" in payload["error"]["details"]
    teardown_test_app(app)


def test_register_creates_buyer_and_sets_session_cookie():
    app = setup_test_app()

    response = app.test_client().post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "Secondhand2026",
            "first_name": "Second",
            "last_name": "Buyer",
            "role": "buyer",
        },
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["success"] is True
    assert payload["data"]["authenticated"] is True
    assert payload["data"]["user"]["email"] == "buyer@example.com"
    assert "secondmarket_session=" in response.headers["Set-Cookie"]

    with app.app_context():
        assert User.query.filter_by(email="buyer@example.com").count() == 1
        assert AuthSession.query.count() == 1

    teardown_test_app(app)


def test_register_rejects_public_admin_registration():
    app = setup_test_app()

    response = app.test_client().post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "AdminSeller2026",
            "first_name": "Admin",
            "last_name": "Seller",
            "role": "admin",
        },
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert "role" in payload["error"]["details"]
    teardown_test_app(app)


def test_login_rejects_invalid_payload():
    app = setup_test_app()

    response = app.test_client().post("/api/v1/auth/login", json={"email": "bad"})
    payload = response.get_json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert "email" in payload["error"]["details"]
    assert "password" in payload["error"]["details"]
    teardown_test_app(app)


def test_login_sets_session_cookie_for_valid_credentials():
    app = setup_test_app()
    with app.app_context():
        user = User(email="buyer@example.com", role="buyer", first_name="Second", last_name="Buyer")
        user.set_password("Secondhand2026")
        db.session.add(user)
        db.session.commit()

    response = app.test_client().post(
        "/api/v1/auth/login",
        json={"email": "buyer@example.com", "password": "Secondhand2026"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["authenticated"] is True
    assert "secondmarket_session=" in response.headers["Set-Cookie"]
    teardown_test_app(app)


def test_login_rejects_invalid_credentials():
    app = setup_test_app()

    response = app.test_client().post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "Secondhand2026"},
    )
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "invalid_credentials"
    teardown_test_app(app)


def test_current_user_contract_reports_unauthenticated_state():
    app = setup_test_app()

    response = app.test_client().get("/api/v1/auth/me")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"] == {"authenticated": False, "user": None}
    teardown_test_app(app)


def test_current_user_loads_authenticated_session_and_logout_revokes_it():
    app = setup_test_app()
    client = app.test_client()
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "Secondhand2026",
            "first_name": "Second",
            "last_name": "Buyer",
            "role": "buyer",
        },
    )

    assert register_response.status_code == 201

    me_response = client.get("/api/v1/auth/me")
    me_payload = me_response.get_json()

    assert me_response.status_code == 200
    assert me_payload["data"]["authenticated"] is True
    assert me_payload["data"]["user"]["email"] == "buyer@example.com"

    response = client.post("/api/v1/auth/logout")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["authenticated"] is False

    with app.app_context():
        assert AuthSession.query.one().is_revoked is True

    teardown_test_app(app)
