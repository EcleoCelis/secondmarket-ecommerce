from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Product
from backend.app.seed import seed_development_data


def setup_tracking_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_tracking_app(app):
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


def checkout_payload():
    return {
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


def create_order(client, product_slug="pre-owned-wireless-headphones"):
    client.post("/api/v1/cart/items", json={"product_slug": product_slug, "quantity": 1})
    response = client.post("/api/v1/checkout/confirm", json=checkout_payload())
    return response.get_json()["data"]["order"]["order_number"]


def test_buyer_can_cancel_order_before_fulfillment_begins_and_stock_is_restored():
    app = setup_tracking_app()
    buyer_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order(buyer_client)

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        quantity_after_checkout = product.quantity

    response = buyer_client.patch(f"/api/v1/orders/{order_number}/cancel")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["message"] == "Order cancelled."
    assert payload["data"]["status"] == "cancelled"
    assert payload["data"]["shipping_status"] == "not_ready"

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        assert product.quantity == quantity_after_checkout + 1

    teardown_tracking_app(app)


def test_buyer_cannot_cancel_order_after_fulfillment_begins():
    app = setup_tracking_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order(buyer_client)

    login_admin(admin_client)
    admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"order_status": "processing", "shipping_status": "ready"},
    )

    response = buyer_client.patch(f"/api/v1/orders/{order_number}/cancel")
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "order_action_not_allowed"
    assert "order_status" in payload["error"]["details"]
    assert "shipping_status" in payload["error"]["details"]

    teardown_tracking_app(app)


def test_buyer_order_detail_exposes_admin_tracking_updates():
    app = setup_tracking_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order(buyer_client)

    login_admin(admin_client)
    admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"shipping_status": "shipped", "tracking_number": "SM-TRACK-2002"},
    )

    response = buyer_client.get(f"/api/v1/orders/{order_number}")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["data"]["shipping_status"] == "shipped"
    assert payload["data"]["shipping_record"]["tracking_number"] == "SM-TRACK-2002"

    teardown_tracking_app(app)


def test_buyer_cancel_route_requires_buyer_owner():
    app = setup_tracking_app()
    first_client = app.test_client()
    second_client = app.test_client()

    register_buyer(first_client, email="first@example.com")
    order_number = create_order(first_client)

    register_buyer(second_client, email="second@example.com")
    response = second_client.patch(f"/api/v1/orders/{order_number}/cancel")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "order_not_found"

    teardown_tracking_app(app)
