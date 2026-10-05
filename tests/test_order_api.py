from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Order, Product
from backend.app.seed import seed_development_data


def setup_order_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_order_app(app):
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


def create_buyer_order(client, product_slug="pre-owned-wireless-headphones"):
    client.post("/api/v1/cart/items", json={"product_slug": product_slug, "quantity": 1})
    response = client.post("/api/v1/checkout/confirm", json=checkout_payload())
    return response.get_json()["data"]["order"]["order_number"]


def test_buyer_can_list_and_view_own_orders():
    app = setup_order_app()
    client = app.test_client()

    register_buyer(client)
    order_number = create_buyer_order(client)

    list_response = client.get("/api/v1/orders")
    list_payload = list_response.get_json()

    assert list_response.status_code == 200
    assert list_payload["meta"]["scope"] == "buyer"
    assert list_payload["meta"]["count"] == 1
    assert list_payload["data"][0]["order_number"] == order_number
    assert list_payload["data"][0]["status"] == "confirmed"
    assert list_payload["data"][0]["item_count"] == 1

    detail_response = client.get(f"/api/v1/orders/{order_number}")
    detail_payload = detail_response.get_json()

    assert detail_response.status_code == 200
    assert detail_payload["data"]["order_number"] == order_number
    assert detail_payload["data"]["items"][0]["product_title"] == "Pre-Owned Wireless Headphones"
    assert detail_payload["data"]["payments"][0]["method"] == "cash_on_delivery"
    assert detail_payload["data"]["shipping_record"]["city"] == "Tagbilaran"

    teardown_order_app(app)


def test_buyer_cannot_view_another_buyers_order():
    app = setup_order_app()
    first_client = app.test_client()
    second_client = app.test_client()

    register_buyer(first_client, email="first@example.com")
    order_number = create_buyer_order(first_client)

    register_buyer(second_client, email="second@example.com")
    response = second_client.get(f"/api/v1/orders/{order_number}")
    payload = response.get_json()

    assert response.status_code == 404
    assert payload["error"]["code"] == "order_not_found"

    teardown_order_app(app)


def test_order_routes_enforce_role_boundaries():
    app = setup_order_app()
    client = app.test_client()

    anonymous_response = client.get("/api/v1/orders")
    assert anonymous_response.status_code == 401

    login_admin(client)
    buyer_route_as_admin = client.get("/api/v1/orders")
    assert buyer_route_as_admin.status_code == 403

    teardown_order_app(app)


def test_admin_can_list_and_view_all_orders_with_buyer_details():
    app = setup_order_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    with app.app_context():
        product = Product.query.filter_by(slug="pre-owned-wireless-headphones").one()
        product.quantity = 2
        db.session.commit()

    register_buyer(buyer_client)
    order_number = create_buyer_order(buyer_client)

    login_admin(admin_client)
    list_response = admin_client.get("/api/v1/admin/orders")
    list_payload = list_response.get_json()

    assert list_response.status_code == 200
    assert list_payload["meta"]["scope"] == "admin"
    assert list_payload["meta"]["count"] == 1
    assert list_payload["data"][0]["buyer"]["email"] == "buyer@example.com"

    detail_response = admin_client.get(f"/api/v1/admin/orders/{order_number}")
    detail_payload = detail_response.get_json()

    assert detail_response.status_code == 200
    assert detail_payload["data"]["buyer"]["email"] == "buyer@example.com"
    assert detail_payload["data"]["shipping_record"]["recipient_name"] == "Second Buyer"

    teardown_order_app(app)


def test_admin_order_filters_are_validated_and_applied():
    app = setup_order_app()
    buyer_client = app.test_client()
    admin_client = app.test_client()

    register_buyer(buyer_client)
    create_buyer_order(buyer_client)

    login_admin(admin_client)
    filtered_response = admin_client.get("/api/v1/admin/orders", query_string={"status": "confirmed"})
    filtered_payload = filtered_response.get_json()

    assert filtered_response.status_code == 200
    assert filtered_payload["meta"]["count"] == 1

    invalid_response = admin_client.get(
        "/api/v1/admin/orders",
        query_string={"status": "packed", "payment_status": "waiting", "shipping_status": "lost", "sort": "random"},
    )
    invalid_payload = invalid_response.get_json()

    assert invalid_response.status_code == 422
    assert "status" in invalid_payload["error"]["details"]
    assert "payment_status" in invalid_payload["error"]["details"]
    assert "shipping_status" in invalid_payload["error"]["details"]
    assert "sort" in invalid_payload["error"]["details"]

    with app.app_context():
        assert Order.query.count() == 1

    teardown_order_app(app)
