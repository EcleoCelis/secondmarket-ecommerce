from enum import StrEnum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates

from backend.app.extensions import db
from backend.app.models.base import IntPrimaryKeyMixin, TimestampMixin, utc_now


class ProductCondition(StrEnum):
    NEW_OTHER = "new_other"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    FOR_REPAIR = "for_repair"


class ProductStatus(StrEnum):
    DRAFT = "draft"
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    HIDDEN = "hidden"


class Category(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "categories"

    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(140), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    parent = db.relationship("Category", remote_side="Category.id", back_populates="children")
    children = db.relationship("Category", back_populates="parent")
    products = db.relationship("Product", back_populates="category", lazy="selectin")

    @validates("name", "slug")
    def validate_required_text(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError(f"Category {key} is required.")
        return cleaned


class Product(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="ck_products_price_cents_nonnegative"),
        CheckConstraint("quantity >= 0", name="ck_products_quantity_nonnegative"),
    )

    seller_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(32), nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default=ProductStatus.DRAFT.value, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    brand = db.Column(db.String(120), nullable=True)
    color = db.Column(db.String(80), nullable=True)
    material = db.Column(db.String(120), nullable=True)
    dimensions = db.Column(db.String(160), nullable=True)
    listed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    seller = db.relationship("User", back_populates="products")
    category = db.relationship("Category", back_populates="products")
    images = db.relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImage.sort_order",
    )
    wishlist_items = db.relationship(
        "WishlistItem",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reviews = db.relationship("Review", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    reports = db.relationship("ProductReport", back_populates="product", cascade="all, delete-orphan", lazy="selectin")

    @validates("title", "slug", "description")
    def validate_required_text(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError(f"Product {key} is required.")
        return cleaned

    @validates("condition")
    def validate_condition(self, key, value):
        if value not in {condition.value for condition in ProductCondition}:
            raise ValueError("Product condition is not supported.")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in ProductStatus}:
            raise ValueError("Product status is not supported.")
        return value

    def publish(self):
        self.status = ProductStatus.AVAILABLE.value
        self.listed_at = utc_now()

    @property
    def is_available(self):
        return self.status == ProductStatus.AVAILABLE.value and self.quantity > 0


class ProductImage(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "product_images"
    __table_args__ = (
        UniqueConstraint("product_id", "sort_order", name="uq_product_images_product_sort_order"),
    )

    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(180), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_primary = db.Column(db.Boolean, nullable=False, default=False, index=True)

    product = db.relationship("Product", back_populates="images")

    @validates("image_url", "alt_text")
    def validate_required_text(self, key, value):
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError(f"Product image {key} is required.")
        return cleaned


class WishlistItem(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_items_user_product"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlist_items")
