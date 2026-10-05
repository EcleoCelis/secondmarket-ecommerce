import pytest

from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import (
    Category,
    Order,
    Product,
    ProductCondition,
    ProductReport,
    ReportReason,
    ReportStatus,
    Review,
    User,
)


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def make_user(email, role=Role.BUYER.value):
    user = User(email=email, role=role, first_name="Second", last_name="User")
    user.set_password("Secondhand2026")
    return user


def make_product():
    seller = make_user("admin@example.com", Role.ADMIN.value)
    category = Category(name="Furniture", slug="furniture")
    return Product(
        seller=seller,
        category=category,
        title="Bookshelf",
        slug="bookshelf",
        description="Used bookshelf.",
        price_cents=200000,
        condition=ProductCondition.GOOD.value,
        quantity=1,
    )


def test_review_links_user_product_and_order(app):
    buyer = make_user("buyer@example.com")
    product = make_product()
    order = Order(user=buyer, order_number="SC-20001")
    review = Review(user=buyer, product=product, order=order, rating=5, title="Great find")

    db.session.add(review)
    db.session.commit()

    assert review.product.title == "Bookshelf"
    assert review.user.email == "buyer@example.com"
    assert product.reviews[0].rating == 5


def test_review_rejects_rating_outside_supported_range(app):
    with pytest.raises(ValueError):
        Review(user=make_user("buyer@example.com"), product=make_product(), rating=6)


def test_product_report_can_be_resolved_by_admin(app):
    reporter = make_user("buyer@example.com")
    admin = make_user("resolver@example.com", Role.ADMIN.value)
    product = make_product()
    report = ProductReport(
        product=product,
        reporter=reporter,
        reason=ReportReason.MISLEADING.value,
        details="Photos do not match item condition.",
    )

    report.resolve(admin, ReportStatus.RESOLVED.value)
    db.session.add(report)
    db.session.commit()

    assert report.status == ReportStatus.RESOLVED.value
    assert report.resolved_by.email == "resolver@example.com"
    assert report.resolved_at is not None


def test_product_report_rejects_unknown_reason_and_invalid_resolution(app):
    with pytest.raises(ValueError):
        ProductReport(product=make_product(), reporter=make_user("buyer@example.com"), reason="unknown")

    report = ProductReport(product=make_product(), reporter=make_user("buyer@example.com"), reason=ReportReason.OTHER.value)

    with pytest.raises(ValueError):
        report.resolve(make_user("admin@example.com", Role.ADMIN.value), ReportStatus.OPEN.value)
