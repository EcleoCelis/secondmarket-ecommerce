from backend.app import create_app
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.seed import seed_development_data


def setup_marketplace_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_marketplace_app(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_marketplace_categories_include_product_counts():
    app = setup_marketplace_app()

    response = app.test_client().get("/api/v1/marketplace/categories")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    categories = {category["slug"]: category for category in payload["data"]}
    assert categories["electronics"]["product_count"] == 3
    assert categories["fashion"]["product_count"] == 5

    teardown_marketplace_app(app)


def test_marketplace_product_listing_uses_local_product_images():
    app = setup_marketplace_app()

    response = app.test_client().get("/api/v1/marketplace/products")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["meta"]["count"] == 8
    first_product = payload["data"][0]
    assert first_product["primary_image"]["url"].startswith("/static/productImages/")
    assert first_product["price"]["currency"] == "PHP"

    teardown_marketplace_app(app)


def test_marketplace_product_listing_supports_category_search_and_sort():
    app = setup_marketplace_app()

    response = app.test_client().get(
        "/api/v1/marketplace/products",
        query_string={"category": "electronics", "q": "watch", "sort": "price_asc"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["slug"] == "minimal-analog-watch"

    teardown_marketplace_app(app)


def test_marketplace_product_detail_returns_images_and_seller():
    app = setup_marketplace_app()

    response = app.test_client().get("/api/v1/marketplace/products/pre-owned-wireless-headphones")
    payload = response.get_json()

    assert response.status_code == 200
    product = payload["data"]
    assert product["slug"] == "pre-owned-wireless-headphones"
    assert product["seller"]["name"] == "SecondMarket Admin"
    assert product["images"][0]["url"] == "/static/productImages/headphones/m502t0016_13june22_headphone_03.jpg"

    teardown_marketplace_app(app)


def test_marketplace_product_filters_validate_price_and_sort():
    app = setup_marketplace_app()

    response = app.test_client().get(
        "/api/v1/marketplace/products",
        query_string={"sort": "unsupported", "min_price_cents": "500", "max_price_cents": "100"},
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert "sort" in payload["error"]["details"]
    assert "price" in payload["error"]["details"]

    teardown_marketplace_app(app)


def test_marketplace_products_support_condition_and_price_filters():
    app = setup_marketplace_app()

    response = app.test_client().get(
        "/api/v1/marketplace/products",
        query_string={
            "category": "fashion",
            "condition": "good",
            "max_price_cents": "70000",
            "sort": "title_asc",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert [product["slug"] for product in payload["data"]] == [
        "pre-loved-student-backpack",
        "soft-sleepwear-set",
    ]

    teardown_marketplace_app(app)


def test_marketplace_product_filters_validate_condition():
    app = setup_marketplace_app()

    response = app.test_client().get(
        "/api/v1/marketplace/products",
        query_string={"condition": "mint"},
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert "condition" in payload["error"]["details"]

    teardown_marketplace_app(app)
