from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Product, ProductStatus
from backend.app.seed import seed_development_data


def setup_checkout_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_checkout_app(app):
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


def valid_checkout_payload(**overrides):
    payload = {
        "shipping_address": {
            "recipient_name": "Second Buyer",
            "phone": "09171234567",
            "address_line1": "123 Reuse Street",
            "address_line2": "Unit 2",
            "city": "Tagbilaran",
            "province": "Bohol",
            "postal_code": "6300",
            "country": "Philippines",
        },
        "payment_method": "cash_on_delivery",
    }
    payload.update(overrides)
    return payload


def test_checkout_draft_requires_buyer_role():
    app = setup_checkout_app()
    client = app.test_client()

    anonymous_response = client.post("/api/v1/checkout/draft", json=valid_checkout_payload())
    assert anonymous_response.status_code == 401

    login_admin(client)
    admin_response = client.post("/api/v1/checkout/draft", json=valid_checkout_payload())
    assert admin_response.status_code == 403
    assert admin_response.get_json()["error"]["code"] == "permission_denied"

    teardown_checkout_app(app)


def test_checkout_draft_validates_shipping_and_payment_payload():
    app = setup_checkout_app()
    client = app.test_client()

    register_buyer(client)
    response = client.post(
        "/api/v1/checkout/draft",
        json={
            "shipping_address": {
                "recipient_name": "",
                "phone": "",
                "address_line1": "",
                "city": "",
                "province": "",
                "postal_code": "",
            },
            "payment_method": "credit_card",
        },
    )
    payload = response.get_json()

    assert response.status_code == 422
    details = payload["error"]["details"]
    assert "shipping_address.recipient_name" in details
    assert "shipping_address.phone" in details
    assert "shipping_address.address_line1" in details
    assert "shipping_address.city" in details
    assert "shipping_address.province" in details
    assert "shipping_address.postal_code" in details
    assert "payment_method" in details

    teardown_checkout_app(app)


def test_checkout_draft_rejects_empty_cart():
    app = setup_checkout_app()
    client = app.test_client()

    register_buyer(client)
    response = client.post("/api/v1/checkout/draft", json=valid_checkout_payload())
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "cart_empty"

    teardown_checkout_app(app)


def test_checkout_draft_returns_server_calculated_order_summary():
    app = setup_checkout_app()
    client = app.test_client()

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.quantity = 3
        db.session.commit()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 2})

    response = client.post("/api/v1/checkout/draft", json=valid_checkout_payload())
    payload = response.get_json()

    assert response.status_code == 200
    draft = payload["data"]
    assert draft["payment_method"] == "cash_on_delivery"
    assert draft["shipping_address"]["city"] == "Tagbilaran"
    assert draft["items"][0]["product_slug"] == "pre-owned-wireless-headphones"
    assert draft["items"][0]["quantity"] == 2
    assert draft["totals"]["subtotal"]["amount_cents"] == 370000
    assert draft["totals"]["shipping"]["amount_cents"] == 0
    assert draft["totals"]["total"]["amount_cents"] == 370000

    teardown_checkout_app(app)


def test_checkout_draft_revalidates_cart_availability():
    app = setup_checkout_app()
    client = app.test_client()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1})

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.status = ProductStatus.SOLD.value
        product.quantity = 0
        db.session.commit()

    response = client.post("/api/v1/checkout/draft", json=valid_checkout_payload())
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "cart_not_checkout_ready"
    assert "pre-owned-wireless-headphones" in payload["error"]["details"]["items"]

    teardown_checkout_app(app)
