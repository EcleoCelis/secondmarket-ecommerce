from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Cart, Product, ProductStatus
from backend.app.seed import seed_development_data


def setup_cart_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_cart_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register_buyer(client, email="buyer@example.com"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Secondhand2026",
            "first_name": "Second",
            "last_name": "Buyer",
            "role": Role.BUYER.value,
        },
    )


def login_admin(client):
    return client.post(
        "/api/v1/auth/login",
        json={"email": "admin@secondmarket.test", "password": "AdminSeller2026"},
    )


def test_cart_requires_buyer_role():
    app = setup_cart_app()
    client = app.test_client()

    anonymous_response = client.get("/api/v1/cart")
    assert anonymous_response.status_code == 401

    login_admin(client)
    admin_response = client.get("/api/v1/cart")
    assert admin_response.status_code == 403
    assert admin_response.get_json()["error"]["code"] == "permission_denied"

    teardown_cart_app(app)


def test_buyer_can_view_empty_cart_and_add_available_product():
    app = setup_cart_app()
    client = app.test_client()

    register_buyer(client)
    empty_response = client.get("/api/v1/cart")
    empty_payload = empty_response.get_json()

    assert empty_response.status_code == 200
    assert empty_payload["data"]["items"] == []
    assert empty_payload["data"]["total_items"] == 0

    add_response = client.post(
        "/api/v1/cart/items",
        json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1},
    )
    add_payload = add_response.get_json()

    assert add_response.status_code == 201
    assert add_payload["data"]["total_items"] == 1
    assert add_payload["data"]["subtotal"]["amount_cents"] == 185000
    assert add_payload["data"]["items"][0]["product"]["slug"] == "pre-owned-wireless-headphones"

    with app.app_context():
        assert Cart.query.count() == 1

    teardown_cart_app(app)


def test_cart_add_validates_payload_and_stock():
    app = setup_cart_app()
    client = app.test_client()

    register_buyer(client)
    invalid_response = client.post("/api/v1/cart/items", json={"product_slug": "", "quantity": 0})
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "product_slug" in invalid_payload["error"]["details"]
    assert "quantity" in invalid_payload["error"]["details"]

    stock_response = client.post(
        "/api/v1/cart/items",
        json={"product_slug": "pre-owned-wireless-headphones", "quantity": 2},
    )
    stock_payload = stock_response.get_json()

    assert stock_response.status_code == 409
    assert stock_payload["error"]["code"] == "insufficient_stock"

    teardown_cart_app(app)


def test_buyer_can_update_and_remove_cart_item():
    app = setup_cart_app()
    client = app.test_client()

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.quantity = 3
        db.session.commit()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 2})

    update_response = client.patch(
        "/api/v1/cart/items/pre-owned-wireless-headphones",
        json={"quantity": 1},
    )
    update_payload = update_response.get_json()

    assert update_response.status_code == 200
    assert update_payload["data"]["total_items"] == 1
    assert update_payload["data"]["items"][0]["quantity"] == 1

    remove_response = client.delete("/api/v1/cart/items/pre-owned-wireless-headphones")
    remove_payload = remove_response.get_json()

    assert remove_response.status_code == 200
    assert remove_payload["data"]["items"] == []
    assert remove_payload["data"]["subtotal"]["amount_cents"] == 0

    teardown_cart_app(app)


def test_cart_rejects_unavailable_products_and_missing_items():
    app = setup_cart_app()
    client = app.test_client()

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.status = ProductStatus.SOLD.value
        product.quantity = 0
        db.session.commit()

    register_buyer(client)
    add_response = client.post(
        "/api/v1/cart/items",
        json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1},
    )
    add_payload = add_response.get_json()

    assert add_response.status_code == 409
    assert add_payload["error"]["code"] == "product_unavailable"

    remove_response = client.delete("/api/v1/cart/items/secondhand-smartphone")
    remove_payload = remove_response.get_json()

    assert remove_response.status_code == 404
    assert remove_payload["error"]["code"] == "cart_item_not_found"

    teardown_cart_app(app)
