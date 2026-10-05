from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Product, ProductCondition, ProductStatus
from backend.app.seed import seed_development_data


def setup_mutation_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
    return app


def teardown_mutation_app(app):
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


def valid_product_payload(**overrides):
    payload = {
        "title": "Vintage Desk Lamp",
        "category_slug": "furniture",
        "description": "Working desk lamp with a clean shade and minor signs of use.",
        "price_cents": 145000,
        "condition": ProductCondition.GOOD.value,
        "status": ProductStatus.AVAILABLE.value,
        "quantity": 1,
        "brand": "HomeLight",
        "color": "Brass",
        "material": "Metal",
        "dimensions": "40cm height",
        "images": [
            {
                "image_url": "/static/productImages/bags/young-girl-with-gray-student-backpack.jpg",
                "alt_text": "Vintage desk lamp",
                "sort_order": 0,
                "is_primary": True,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_admin_can_create_product_with_images_and_generated_slug():
    app = setup_mutation_app()
    client = app.test_client()

    login_admin(client)
    response = client.post("/api/v1/admin/products", json=valid_product_payload())
    payload = response.get_json()

    assert response.status_code == 201
    product = payload["data"]
    assert product["slug"] == "vintage-desk-lamp"
    assert product["status"] == ProductStatus.AVAILABLE.value
    assert product["seller"]["email"] == "admin@secondmarket.test"
    assert product["primary_image"]["url"].startswith("/static/productImages/")
    assert product["listed_at"] is not None

    with app.app_context():
        saved_product = Product.query.filter_by(slug="vintage-desk-lamp").one()
        assert saved_product.images[0].is_primary is True
        assert saved_product.category.slug == "furniture"

    teardown_mutation_app(app)


def test_admin_product_create_requires_admin_role():
    app = setup_mutation_app()
    client = app.test_client()

    anonymous_response = client.post("/api/v1/admin/products", json=valid_product_payload())
    assert anonymous_response.status_code == 401

    register_buyer(client)
    buyer_response = client.post("/api/v1/admin/products", json=valid_product_payload(slug="buyer-product"))
    assert buyer_response.status_code == 403

    teardown_mutation_app(app)


def test_product_create_validates_payload_shape():
    app = setup_mutation_app()
    client = app.test_client()

    login_admin(client)
    response = client.post(
        "/api/v1/admin/products",
        json=valid_product_payload(
            title="",
            price_cents=-1,
            quantity=0,
            status=ProductStatus.AVAILABLE.value,
            condition="mint",
            images=[{"image_url": "", "alt_text": ""}],
        ),
    )
    payload = response.get_json()

    assert response.status_code == 422
    details = payload["error"]["details"]
    assert "title" in details
    assert "price_cents" in details
    assert "quantity" in details
    assert "condition" in details
    assert "images.0.image_url" in details
    assert "images.0.alt_text" in details

    teardown_mutation_app(app)


def test_product_create_validates_category_and_slug_uniqueness():
    app = setup_mutation_app()
    client = app.test_client()

    login_admin(client)
    category_response = client.post(
        "/api/v1/admin/products",
        json=valid_product_payload(category_slug="missing-category"),
    )
    category_payload = category_response.get_json()

    assert category_response.status_code == 422
    assert "category_slug" in category_payload["error"]["details"]

    slug_response = client.post(
        "/api/v1/admin/products",
        json=valid_product_payload(slug="pre-owned-wireless-headphones"),
    )
    slug_payload = slug_response.get_json()

    assert slug_response.status_code == 422
    assert "slug" in slug_payload["error"]["details"]

    teardown_mutation_app(app)


def test_admin_can_update_product_and_replace_images():
    app = setup_mutation_app()
    client = app.test_client()

    login_admin(client)
    response = client.put(
        "/api/v1/admin/products/pre-owned-wireless-headphones",
        json={
            "title": "Updated Wireless Headphones",
            "price_cents": 160000,
            "status": ProductStatus.HIDDEN.value,
            "quantity": 3,
            "images": [
                {
                    "image_url": "/static/productImages/headphones/m502t0016_13june22_headphone_03.jpg",
                    "alt_text": "Updated headphones",
                }
            ],
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    product = payload["data"]
    assert product["title"] == "Updated Wireless Headphones"
    assert product["price"]["amount_cents"] == 160000
    assert product["status"] == ProductStatus.HIDDEN.value
    assert len(product["images"]) == 1
    assert product["images"][0]["is_primary"] is True

    teardown_mutation_app(app)


def test_product_update_rejects_slug_conflict_and_missing_product():
    app = setup_mutation_app()
    client = app.test_client()

    login_admin(client)
    conflict_response = client.put(
        "/api/v1/admin/products/pre-owned-wireless-headphones",
        json={"slug": "secondhand-smartphone"},
    )
    conflict_payload = conflict_response.get_json()

    assert conflict_response.status_code == 422
    assert "slug" in conflict_payload["error"]["details"]

    missing_response = client.put("/api/v1/admin/products/missing-product", json={"title": "Missing"})
    missing_payload = missing_response.get_json()

    assert missing_response.status_code == 404
    assert missing_payload["error"]["code"] == "product_not_found"

    teardown_mutation_app(app)
