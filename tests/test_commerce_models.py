import pytest

from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Payment,
    PaymentStatus,
    Product,
    ProductCondition,
    ShippingRecord,
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


def make_user(email="buyer@example.com", role=Role.BUYER.value):
    user = User(email=email, role=role, first_name="Second", last_name="Buyer")
    user.set_password("Secondhand2026")
    return user


def make_product():
    seller = make_user("admin@example.com", Role.ADMIN.value)
    category = Category(name="Furniture", slug="furniture")
    return Product(
        seller=seller,
        category=category,
        title="Wooden Chair",
        slug="wooden-chair",
        description="Pre-loved chair.",
        price_cents=120000,
        condition=ProductCondition.GOOD.value,
        quantity=1,
    )


def test_cart_item_calculates_subtotal(app):
    buyer = make_user()
    product = make_product()
    cart = Cart(user=buyer)
    cart.items.append(CartItem(product=product, quantity=2, unit_price_cents=product.price_cents))

    db.session.add(cart)
    db.session.commit()

    assert cart.items[0].line_total_cents == 240000
    assert cart.subtotal_cents == 240000


def test_cart_item_rejects_invalid_quantity(app):
    with pytest.raises(ValueError):
        CartItem(product=make_product(), quantity=0, unit_price_cents=120000)


def test_order_recalculates_totals_and_tracks_payment_shipping(app):
    buyer = make_user()
    product = make_product()
    order = Order(user=buyer, order_number="SC-10001", shipping_cents=5000)
    order.items.append(OrderItem(product=product, product_title=product.title, quantity=1, unit_price_cents=product.price_cents))
    order.payments.append(Payment(method="cash_on_delivery", amount_cents=125000, status=PaymentStatus.PENDING.value))
    order.shipping_record = ShippingRecord(
        recipient_name="Second Buyer",
        phone="09171234567",
        address_line1="123 Market Street",
        city="Tagbilaran",
        province="Bohol",
        postal_code="6300",
    )

    order.recalculate_totals()
    order.mark_placed()

    db.session.add(order)
    db.session.commit()

    assert order.subtotal_cents == 120000
    assert order.total_cents == 125000
    assert order.placed_at is not None
    assert order.payments[0].method == "cash_on_delivery"
    assert order.shipping_record.city == "Tagbilaran"


def test_order_rejects_invalid_status_and_negative_amount(app):
    with pytest.raises(ValueError):
        Order(user=make_user(), order_number="SC-10002", status="unknown")

    with pytest.raises(ValueError):
        Payment(method="cash_on_delivery", amount_cents=-1)
