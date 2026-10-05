from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Order, Product
from backend.app.seed import seed_development_data


def setup_fulfillment_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_fulfillment_app(app):
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


def create_order_for_fulfillment(client):
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1})
    response = client.post("/api/v1/checkout/confirm", json=checkout_payload())
    return response.get_json()["data"]["order"]["order_number"]


def test_admin_can_update_order_payment_shipping_and_tracking_status():
    app = setup_fulfillment_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.quantity = 2
        db.session.commit()

    register_buyer(buyer_client)
    order_number = create_order_for_fulfillment(buyer_client)
    login_admin(admin_client)

    response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={
            "order_status": "processing",
            "payment_status": "paid",
            "shipping_status": "ready",
            "tracking_number": "SM-TRACK-1001",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["message"] == "Order fulfillment updated."
    assert payload["data"]["status"] == "processing"
    assert payload["data"]["payment_status"] == "paid"
    assert payload["data"]["shipping_status"] == "ready"
    assert payload["data"]["payments"][0]["status"] == "paid"
    assert payload["data"]["shipping_record"]["status"] == "ready"
    assert payload["data"]["shipping_record"]["tracking_number"] == "SM-TRACK-1001"

    teardown_fulfillment_app(app)


def test_admin_fulfillment_update_validates_status_values_and_transitions():
    app = setup_fulfillment_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order_for_fulfillment(buyer_client)
    login_admin(admin_client)

    invalid_value_response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={
            "order_status": "packed",
            "payment_status": "waiting",
            "shipping_status": "lost",
        },
    )
    invalid_value_payload = invalid_value_response.get_json()

    assert invalid_value_response.status_code == 422
    assert "order_status" in invalid_value_payload["error"]["details"]
    assert "payment_status" in invalid_value_payload["error"]["details"]
    assert "shipping_status" in invalid_value_payload["error"]["details"]

    invalid_transition_response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"order_status": "delivered"},
    )
    invalid_transition_payload = invalid_transition_response.get_json()

    assert invalid_transition_response.status_code == 422
    assert "Cannot change from confirmed to delivered." in invalid_transition_payload["error"]["details"]["order_status"]

    teardown_fulfillment_app(app)


def test_admin_must_add_tracking_before_marking_order_shipped():
    app = setup_fulfillment_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order_for_fulfillment(buyer_client)
    login_admin(admin_client)

    response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"shipping_status": "shipped"},
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert "tracking_number" in payload["error"]["details"]

    teardown_fulfillment_app(app)


def test_terminal_cancelled_order_cannot_be_fulfilled():
    app = setup_fulfillment_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order_for_fulfillment(buyer_client)
    login_admin(admin_client)

    cancel_response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"order_status": "cancelled"},
    )
    assert cancel_response.status_code == 200

    response = admin_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"order_status": "processing"},
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert "Cannot change from cancelled to processing." in payload["error"]["details"]["order_status"]

    teardown_fulfillment_app(app)


def test_fulfillment_update_requires_admin_role():
    app = setup_fulfillment_app()
    buyer_client = app.test_client()

    register_buyer(buyer_client)
    order_number = create_order_for_fulfillment(buyer_client)

    response = buyer_client.patch(
        f"/api/v1/admin/orders/{order_number}/fulfillment",
        json={"order_status": "processing"},
    )

    assert response.status_code == 403

    teardown_fulfillment_app(app)
