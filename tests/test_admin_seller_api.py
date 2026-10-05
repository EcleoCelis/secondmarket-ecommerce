from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Category, Product, ProductCondition, ProductImage, ProductStatus, User
from backend.app.seed import seed_development_data


def setup_admin_app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_development_data()
        admin = User.query.filter_by(email="admin@secondmarket.test").one()
        category = Category.query.filter_by(slug="electronics").one()
        draft = Product(
            seller=admin,
            category=category,
            title="Draft Console Bundle",
            slug="draft-console-bundle",
            description="Draft listing reserved for admin inventory review.",
            price_cents=350000,
            condition=ProductCondition.GOOD.value,
            status=ProductStatus.DRAFT.value,
            quantity=2,
            brand="GameBox",
            color="Black",
            material="Plastic",
        )
        draft.images.append(
            ProductImage(
                image_url="/static/productImages/smartphones/330788-P9NVVS-165.jpg",
                alt_text="Draft console bundle",
                sort_order=0,
                is_primary=True,
            )
        )
        db.session.add(draft)
        db.session.commit()
    return app


def teardown_admin_app(app):
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


def test_admin_categories_require_admin_role():
    app = setup_admin_app()
    client = app.test_client()

    anonymous_response = client.get("/api/v1/admin/categories")
    assert anonymous_response.status_code == 401

    register_buyer(client)
    buyer_response = client.get("/api/v1/admin/categories")
    assert buyer_response.status_code == 403
    assert buyer_response.get_json()["error"]["code"] == "permission_denied"

    teardown_admin_app(app)


def test_admin_can_list_categories_with_total_product_counts():
    app = setup_admin_app()
    client = app.test_client()

    login_admin(client)
    response = client.get("/api/v1/admin/categories")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["meta"]["scope"] == "admin"
    categories = {category["slug"]: category for category in payload["data"]}
    assert categories["electronics"]["product_count"] == 4
    assert categories["fashion"]["product_count"] == 5

    teardown_admin_app(app)


def test_admin_can_list_products_including_drafts():
    app = setup_admin_app()
    client = app.test_client()

    login_admin(client)
    response = client.get("/api/v1/admin/products", query_string={"status": "draft"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["slug"] == "draft-console-bundle"
    assert payload["data"][0]["status"] == ProductStatus.DRAFT.value
    assert payload["data"][0]["primary_image"]["url"].startswith("/static/productImages/")

    teardown_admin_app(app)


def test_admin_product_filters_are_validated():
    app = setup_admin_app()
    client = app.test_client()

    login_admin(client)
    response = client.get(
        "/api/v1/admin/products",
        query_string={"status": "archived", "condition": "mint", "sort": "oldest"},
    )
    payload = response.get_json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert "status" in payload["error"]["details"]
    assert "condition" in payload["error"]["details"]
    assert "sort" in payload["error"]["details"]

    teardown_admin_app(app)
