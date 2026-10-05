from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Product, ProductCondition, ProductStatus
from backend.app.seed import seed_development_data


def setup_status_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_status_app(app):
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


def create_draft_product(client, **overrides):
    payload = {
        "title": "Draft Status Workflow Item",
        "category_slug": "electronics",
        "description": "Draft item used for status workflow checks.",
        "price_cents": 99000,
        "condition": ProductCondition.GOOD.value,
        "status": ProductStatus.DRAFT.value,
        "quantity": 1,
    }
    payload.update(overrides)
    return client.post("/api/v1/admin/products", json=payload)


def test_admin_can_publish_hide_reserve_and_mark_sold():
    app = setup_status_app()
    client = app.test_client()

    login_admin(client)
    create_draft_product(client)

    publish_response = client.patch(
        "/api/v1/admin/products/draft-status-workflow-item/status",
        json={"status": ProductStatus.AVAILABLE.value},
    )
    publish_payload = publish_response.get_json()

    assert publish_response.status_code == 200
    assert publish_payload["data"]["status"] == ProductStatus.AVAILABLE.value
    assert publish_payload["data"]["listed_at"] is not None

    hidden_response = client.patch(
        "/api/v1/admin/products/draft-status-workflow-item/status",
        json={"status": ProductStatus.HIDDEN.value},
    )
    assert hidden_response.status_code == 200
    assert hidden_response.get_json()["data"]["status"] == ProductStatus.HIDDEN.value

    reserved_response = client.patch(
        "/api/v1/admin/products/draft-status-workflow-item/status",
        json={"status": ProductStatus.RESERVED.value},
    )
    assert reserved_response.status_code == 200
    assert reserved_response.get_json()["data"]["status"] == ProductStatus.RESERVED.value

    sold_response = client.patch(
        "/api/v1/admin/products/draft-status-workflow-item/status",
        json={"status": ProductStatus.SOLD.value},
    )
    sold_payload = sold_response.get_json()

    assert sold_response.status_code == 200
    assert sold_payload["data"]["status"] == ProductStatus.SOLD.value
    assert sold_payload["data"]["quantity"] == 0

    teardown_status_app(app)


def test_status_workflow_rejects_invalid_status_and_missing_product():
    app = setup_status_app()
    client = app.test_client()

    login_admin(client)
    invalid_response = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/status",
        json={"status": "archived"},
    )
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "status" in invalid_payload["error"]["details"]

    missing_response = client.patch("/api/v1/admin/products/missing/status", json={"status": ProductStatus.HIDDEN.value})
    assert missing_response.status_code == 404
    assert missing_response.get_json()["error"]["code"] == "product_not_found"

    teardown_status_app(app)


def test_cannot_publish_or_reserve_without_stock():
    app = setup_status_app()
    client = app.test_client()

    login_admin(client)
    create_draft_product(client, title="Zero Stock Draft Item", quantity=0)

    publish_response = client.patch(
        "/api/v1/admin/products/zero-stock-draft-item/status",
        json={"status": ProductStatus.AVAILABLE.value},
    )
    publish_payload = publish_response.get_json()

    assert publish_response.status_code == 422
    assert "quantity" in publish_payload["error"]["details"]

    reserve_response = client.patch(
        "/api/v1/admin/products/zero-stock-draft-item/status",
        json={"status": ProductStatus.RESERVED.value},
    )
    reserve_payload = reserve_response.get_json()

    assert reserve_response.status_code == 422
    assert "quantity" in reserve_payload["error"]["details"]

    teardown_status_app(app)


def test_admin_can_update_inventory_quantity():
    app = setup_status_app()
    client = app.test_client()

    login_admin(client)
    response = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/inventory",
        json={"quantity": 5},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["quantity"] == 5

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        assert product.quantity == 5

    teardown_status_app(app)


def test_inventory_update_validates_quantity_and_active_stock_rules():
    app = setup_status_app()
    client = app.test_client()

    login_admin(client)
    invalid_response = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/inventory",
        json={"quantity": -1},
    )
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "quantity" in invalid_payload["error"]["details"]

    zero_response = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/inventory",
        json={"quantity": 0},
    )
    zero_payload = zero_response.get_json()

    assert zero_response.status_code == 422
    assert "quantity" in zero_payload["error"]["details"]

    teardown_status_app(app)


def test_status_and_inventory_routes_require_admin_role():
    app = setup_status_app()
    client = app.test_client()

    anonymous_status = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/status",
        json={"status": ProductStatus.HIDDEN.value},
    )
    assert anonymous_status.status_code == 401

    register_buyer(client)
    buyer_inventory = client.patch(
        "/api/v1/admin/products/pre-owned-wireless-headphones/inventory",
        json={"quantity": 2},
    )
    assert buyer_inventory.status_code == 403

    teardown_status_app(app)
