from enum import StrEnum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates

from backend.app.extensions import db
from backend.app.models.base import IntPrimaryKeyMixin, TimestampMixin, utc_now


class CartStatus(StrEnum):
    ACTIVE = "active"
    CHECKED_OUT = "checked_out"
    ABANDONED = "abandoned"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class ShippingStatus(StrEnum):
    NOT_READY = "not_ready"
    READY = "ready"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"


def validate_nonnegative_amount(value, field_name):
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return value


def validate_positive_quantity(value):
    if value < 1:
        raise ValueError("Quantity must be at least 1.")
    return value


class Cart(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "carts"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default=CartStatus.ACTIVE.value, index=True)

    user = db.relationship("User", back_populates="carts")
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="selectin")

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in CartStatus}:
            raise ValueError("Cart status is not supported.")
        return value

    @property
    def subtotal_cents(self):
        return sum(item.line_total_cents for item in self.items)


class CartItem(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_cart_items_quantity_positive"),
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
    )

    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price_cents = db.Column(db.Integer, nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    @validates("quantity")
    def validate_quantity(self, key, value):
        return validate_positive_quantity(value)

    @validates("unit_price_cents")
    def validate_unit_price(self, key, value):
        return validate_nonnegative_amount(value, "Unit price")

    @property
    def line_total_cents(self):
        return self.quantity * self.unit_price_cents


class Order(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal_cents >= 0", name="ck_orders_subtotal_nonnegative"),
        CheckConstraint("shipping_cents >= 0", name="ck_orders_shipping_nonnegative"),
        CheckConstraint("total_cents >= 0", name="ck_orders_total_nonnegative"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = db.Column(db.String(40), nullable=False, unique=True, index=True)
    status = db.Column(db.String(32), nullable=False, default=OrderStatus.PENDING.value, index=True)
    payment_status = db.Column(db.String(32), nullable=False, default=PaymentStatus.PENDING.value, index=True)
    shipping_status = db.Column(db.String(32), nullable=False, default=ShippingStatus.NOT_READY.value, index=True)
    subtotal_cents = db.Column(db.Integer, nullable=False, default=0)
    shipping_cents = db.Column(db.Integer, nullable=False, default=0)
    total_cents = db.Column(db.Integer, nullable=False, default=0)
    placed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    shipping_record = db.relationship("ShippingRecord", back_populates="order", uselist=False, cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="order", lazy="selectin")

    @validates("status")
    def validate_order_status(self, key, value):
        if value not in {status.value for status in OrderStatus}:
            raise ValueError("Order status is not supported.")
        return value

    @validates("payment_status")
    def validate_payment_status(self, key, value):
        if value not in {status.value for status in PaymentStatus}:
            raise ValueError("Payment status is not supported.")
        return value

    @validates("shipping_status")
    def validate_shipping_status(self, key, value):
        if value not in {status.value for status in ShippingStatus}:
            raise ValueError("Shipping status is not supported.")
        return value

    @validates("subtotal_cents", "shipping_cents", "total_cents")
    def validate_amount(self, key, value):
        return validate_nonnegative_amount(value, key)

    def mark_placed(self):
        self.placed_at = utc_now()

    def recalculate_totals(self):
        self.subtotal_cents = sum(item.line_total_cents for item in self.items)
        self.total_cents = self.subtotal_cents + self.shipping_cents


class OrderItem(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price_cents >= 0", name="ck_order_items_unit_price_nonnegative"),
    )

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_title = db.Column(db.String(180), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price_cents = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @validates("product_title")
    def validate_product_title(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Order item product title is required.")
        return cleaned

    @validates("quantity")
    def validate_quantity(self, key, value):
        return validate_positive_quantity(value)

    @validates("unit_price_cents")
    def validate_unit_price(self, key, value):
        return validate_nonnegative_amount(value, "Unit price")

    @property
    def line_total_cents(self):
        return self.quantity * self.unit_price_cents


class Payment(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "payments"

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    method = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(32), nullable=False, default=PaymentStatus.PENDING.value, index=True)
    amount_cents = db.Column(db.Integer, nullable=False)
    reference_number = db.Column(db.String(120), nullable=True, unique=True)

    order = db.relationship("Order", back_populates="payments")

    @validates("method")
    def validate_method(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("Payment method is required.")
        return cleaned

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in PaymentStatus}:
            raise ValueError("Payment status is not supported.")
        return value

    @validates("amount_cents")
    def validate_amount(self, key, value):
        return validate_nonnegative_amount(value, "Payment amount")


class ShippingRecord(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "shipping_records"

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    recipient_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    address_line1 = db.Column(db.String(180), nullable=False)
    address_line2 = db.Column(db.String(180), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    province = db.Column(db.String(120), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(80), nullable=False, default="Philippines")
    tracking_number = db.Column(db.String(120), nullable=True, unique=True)
    status = db.Column(db.String(32), nullable=False, default=ShippingStatus.NOT_READY.value, index=True)

    order = db.relationship("Order", back_populates="shipping_record")

    @validates("recipient_name", "phone", "address_line1", "city", "province", "postal_code", "country")
    def validate_required_text(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError(f"Shipping {key} is required.")
        return cleaned

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in ShippingStatus}:
            raise ValueError("Shipping status is not supported.")
        return value
