from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Cart, CartStatus, Order, Payment, Product, ProductStatus, ShippingRecord
from backend.app.seed import seed_development_data


def setup_confirmation_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_confirmation_app(app):
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


def test_checkout_confirm_requires_buyer_role():
    app = setup_confirmation_app()
    client = app.test_client()

    anonymous_response = client.post("/api/v1/checkout/confirm", json=valid_checkout_payload())
    assert anonymous_response.status_code == 401

    login_admin(client)
    admin_response = client.post("/api/v1/checkout/confirm", json=valid_checkout_payload())
    assert admin_response.status_code == 403
    assert admin_response.get_json()["error"]["code"] == "permission_denied"

    teardown_confirmation_app(app)


def test_checkout_confirm_creates_order_payment_shipping_and_deducts_inventory():
    app = setup_confirmation_app()
    client = app.test_client()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1})

    response = client.post("/api/v1/checkout/confirm", json=valid_checkout_payload())
    payload = response.get_json()

    assert response.status_code == 201
    confirmation = payload["data"]
    assert confirmation["order"]["order_number"].startswith("SM-")
    assert confirmation["order"]["status"] == "confirmed"
    assert confirmation["order"]["payment_status"] == "pending"
    assert confirmation["order"]["shipping_status"] == "not_ready"
    assert confirmation["items"][0]["product_title"] == "Pre-Owned Wireless Headphones"
    assert confirmation["order"]["subtotal"]["amount_cents"] == 185000
    assert confirmation["order"]["shipping"]["amount_cents"] == 4500
    assert confirmation["order"]["total"]["amount_cents"] == 189500
    assert confirmation["payment"]["method"] == "cash_on_delivery"
    assert confirmation["shipping_address"]["city"] == "Tagbilaran"

    with app.app_context():
        order = Order.query.one()
        payment = Payment.query.one()
        shipping = ShippingRecord.query.one()
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        cart = Cart.query.one()

        assert order.items[0].product_title == "Pre-Owned Wireless Headphones"
        assert payment.amount_cents == 189500
        assert shipping.recipient_name == "Second Buyer"
        assert product.quantity == 0
        assert product.status == ProductStatus.SOLD.value
        assert cart.status == CartStatus.CHECKED_OUT.value

    teardown_confirmation_app(app)


def test_checkout_confirm_creates_new_active_cart_after_successful_checkout():
    app = setup_confirmation_app()
    client = app.test_client()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "secondhand-smartphone", "quantity": 1})
    confirm_response = client.post("/api/v1/checkout/confirm", json=valid_checkout_payload(payment_method="gcash_pending"))
    assert confirm_response.status_code == 201

    cart_response = client.get("/api/v1/cart")
    cart_payload = cart_response.get_json()

    assert cart_response.status_code == 200
    assert cart_payload["data"]["items"] == []

    with app.app_context():
        carts = Cart.query.order_by(Cart.id.asc()).all()
        assert [cart.status for cart in carts] == [CartStatus.CHECKED_OUT.value, CartStatus.ACTIVE.value]

    teardown_confirmation_app(app)


def test_checkout_confirm_revalidates_stock_before_creating_order():
    app = setup_confirmation_app()
    client = app.test_client()

    register_buyer(client)
    client.post("/api/v1/cart/items", json={"product_slug": "pre-owned-wireless-headphones", "quantity": 1})

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.status = ProductStatus.SOLD.value
        product.quantity = 0
        db.session.commit()

    response = client.post("/api/v1/checkout/confirm", json=valid_checkout_payload())
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "cart_not_checkout_ready"

    with app.app_context():
        assert Order.query.count() == 0
        assert Payment.query.count() == 0
        assert ShippingRecord.query.count() == 0

    teardown_confirmation_app(app)
