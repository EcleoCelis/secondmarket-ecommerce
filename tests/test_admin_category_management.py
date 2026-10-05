from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Category
from backend.app.seed import seed_development_data


def setup_category_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_category_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def login_admin(client):
    return client.post(
        "/api/v1/auth/login",
        json={"email": "admin@secondmarket.test", "password": "AdminSeller2026"},
    )


def register_buyer(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@example.com",
            "password": "Secondhand2026",
            "first_name": "Second",
            "last_name": "Buyer",
            "role": Role.BUYER.value,
        },
    )


def test_admin_can_create_category_with_generated_slug():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    response = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Home Decor",
            "description": "Secondhand decor, frames, and small fixtures.",
            "sort_order": 8,
        },
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["data"]["name"] == "Home Decor"
    assert payload["data"]["slug"] == "home-decor"
    assert payload["data"]["is_active"] is True
    assert payload["data"]["sort_order"] == 8

    with app.app_context():
        assert Category.query.filter_by(slug="home-decor").one().description.startswith("Secondhand decor")

    teardown_category_app(app)


def test_category_create_requires_admin_role():
    app = setup_category_app()
    client = app.test_client()

    anonymous_response = client.post("/api/v1/admin/categories", json={"name": "Unauthorized"})
    assert anonymous_response.status_code == 401

    register_buyer(client)
    buyer_response = client.post("/api/v1/admin/categories", json={"name": "Buyer Category"})
    assert buyer_response.status_code == 403

    teardown_category_app(app)


def test_category_create_validates_payload_and_uniqueness():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    invalid_response = client.post(
        "/api/v1/admin/categories",
        json={"name": "", "slug": "Invalid Slug", "sort_order": -1, "is_active": "yes"},
    )
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "name" in invalid_payload["error"]["details"]
    assert "slug" in invalid_payload["error"]["details"]
    assert "sort_order" in invalid_payload["error"]["details"]
    assert "is_active" in invalid_payload["error"]["details"]

    duplicate_slug_response = client.post("/api/v1/admin/categories", json={"name": "Gadgets", "slug": "electronics"})
    duplicate_slug_payload = duplicate_slug_response.get_json()

    assert duplicate_slug_response.status_code == 422
    assert "slug" in duplicate_slug_payload["error"]["details"]

    duplicate_name_response = client.post("/api/v1/admin/categories", json={"name": "Electronics", "slug": "gadgets"})
    duplicate_name_payload = duplicate_name_response.get_json()

    assert duplicate_name_response.status_code == 422
    assert "name" in duplicate_name_payload["error"]["details"]

    teardown_category_app(app)


def test_admin_can_update_category_fields():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    response = client.put(
        "/api/v1/admin/categories/books",
        json={
            "name": "Books and References",
            "slug": "books-references",
            "description": "Used books, references, and study materials.",
            "sort_order": 2,
            "is_active": False,
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["name"] == "Books and References"
    assert payload["data"]["slug"] == "books-references"
    assert payload["data"]["is_active"] is False
    assert payload["data"]["sort_order"] == 2

    teardown_category_app(app)


def test_category_update_rejects_conflicts_and_missing_category():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    conflict_response = client.put("/api/v1/admin/categories/books", json={"slug": "electronics"})
    conflict_payload = conflict_response.get_json()

    assert conflict_response.status_code == 422
    assert "slug" in conflict_payload["error"]["details"]

    missing_response = client.put("/api/v1/admin/categories/missing", json={"name": "Missing"})
    missing_payload = missing_response.get_json()

    assert missing_response.status_code == 404
    assert missing_payload["error"]["code"] == "category_not_found"

    teardown_category_app(app)


def test_admin_can_activate_and_deactivate_category():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    deactivate_response = client.patch("/api/v1/admin/categories/fashion/status", json={"is_active": False})
    deactivate_payload = deactivate_response.get_json()

    assert deactivate_response.status_code == 200
    assert deactivate_payload["data"]["is_active"] is False

    activate_response = client.patch("/api/v1/admin/categories/fashion/status", json={"is_active": True})
    activate_payload = activate_response.get_json()

    assert activate_response.status_code == 200
    assert activate_payload["data"]["is_active"] is True

    teardown_category_app(app)


def test_category_status_validates_boolean_and_missing_category():
    app = setup_category_app()
    client = app.test_client()

    login_admin(client)
    invalid_response = client.patch("/api/v1/admin/categories/fashion/status", json={"is_active": "false"})
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "is_active" in invalid_payload["error"]["details"]

    missing_response = client.patch("/api/v1/admin/categories/missing/status", json={"is_active": False})
    missing_payload = missing_response.get_json()

    assert missing_response.status_code == 404
    assert missing_payload["error"]["code"] == "category_not_found"

    teardown_category_app(app)
