import pytest

from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import Category, Product, ProductCondition, ProductImage, ProductStatus, User


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def make_admin():
    user = User(email="admin@example.com", role=Role.ADMIN.value, first_name="Admin", last_name="Seller")
    user.set_password("AdminSeller2026")
    return user


def test_category_and_product_catalog_relationships(app):
    seller = make_admin()
    category = Category(name="Furniture", slug="furniture", description="Secondhand home furniture")
    product = Product(
        seller=seller,
        category=category,
        title="Solid Wood Desk",
        slug="solid-wood-desk",
        description="Used desk in good condition.",
        price_cents=450000,
        condition=ProductCondition.GOOD.value,
        quantity=1,
    )
    product.images.append(
        ProductImage(image_url="https://example.com/desk.jpg", alt_text="Solid wood desk", sort_order=0, is_primary=True)
    )
    product.publish()

    db.session.add(product)
    db.session.commit()

    assert product.is_available is True
    assert product.status == ProductStatus.AVAILABLE.value
    assert product.category.name == "Furniture"
    assert product.seller.email == "admin@example.com"
    assert product.images[0].is_primary is True


def test_catalog_models_validate_required_and_enum_values(app):
    with pytest.raises(ValueError):
        Category(name="", slug="missing-name")

    with pytest.raises(ValueError):
        Product(
            seller=make_admin(),
            category=Category(name="Furniture", slug="furniture"),
            title="Desk",
            slug="desk",
            description="Description",
            price_cents=1000,
            condition="broken_enum",
        )


def test_unavailable_product_when_quantity_is_zero(app):
    product = Product(
        seller=make_admin(),
        category=Category(name="Furniture", slug="furniture"),
        title="Lamp",
        slug="lamp",
        description="Vintage lamp.",
        price_cents=150000,
        condition=ProductCondition.LIKE_NEW.value,
        quantity=0,
        status=ProductStatus.AVAILABLE.value,
    )

    assert product.is_available is False
