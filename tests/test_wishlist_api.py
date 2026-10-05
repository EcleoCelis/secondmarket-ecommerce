from backend.app import create_app
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import WishlistItem
from backend.app.seed import seed_development_data


def setup_wishlist_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_wishlist_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register_buyer(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": "wishlist-buyer@example.com",
            "password": "Secondhand2026",
            "first_name": "Wishlist",
            "last_name": "Buyer",
            "role": "buyer",
        },
    )


def test_wishlist_requires_authenticated_buyer():
    app = setup_wishlist_app()

    response = app.test_client().get("/api/v1/marketplace/wishlist")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "authentication_required"

    teardown_wishlist_app(app)


def test_buyer_can_add_list_and_remove_wishlist_item():
    app = setup_wishlist_app()
    client = app.test_client()
    register_response = register_buyer(client)
    assert register_response.status_code == 201

    add_response = client.post(
        "/api/v1/marketplace/wishlist",
        json={"product_slug": "pre-owned-wireless-headphones"},
    )
    add_payload = add_response.get_json()

    assert add_response.status_code == 201
    assert add_payload["data"]["slug"] == "pre-owned-wireless-headphones"

    duplicate_response = client.post(
        "/api/v1/marketplace/wishlist",
        json={"product_slug": "pre-owned-wireless-headphones"},
    )
    assert duplicate_response.status_code == 200

    list_response = client.get("/api/v1/marketplace/wishlist")
    list_payload = list_response.get_json()

    assert list_response.status_code == 200
    assert list_payload["meta"]["count"] == 1
    assert list_payload["data"][0]["slug"] == "pre-owned-wireless-headphones"

    remove_response = client.delete("/api/v1/marketplace/wishlist/pre-owned-wireless-headphones")
    remove_payload = remove_response.get_json()

    assert remove_response.status_code == 200
    assert remove_payload["data"]["product_slug"] == "pre-owned-wireless-headphones"

    with app.app_context():
        assert WishlistItem.query.count() == 0

    teardown_wishlist_app(app)


def test_wishlist_rejects_missing_or_unknown_product():
    app = setup_wishlist_app()
    client = app.test_client()
    register_buyer(client)

    missing_response = client.post("/api/v1/marketplace/wishlist", json={})
    missing_payload = missing_response.get_json()

    assert missing_response.status_code == 422
    assert "product_slug" in missing_payload["error"]["details"]

    unknown_response = client.post(
        "/api/v1/marketplace/wishlist",
        json={"product_slug": "missing-product"},
    )
    unknown_payload = unknown_response.get_json()

    assert unknown_response.status_code == 404
    assert unknown_payload["error"]["code"] == "product_not_found"

    teardown_wishlist_app(app)
