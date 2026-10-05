import hashlib
import re
from enum import StrEnum

from sqlalchemy.orm import validates

from backend.app.auth.rbac import Role, is_valid_role
from backend.app.auth.security import hash_password, verify_password
from backend.app.extensions import db
from backend.app.models.base import IntPrimaryKeyMixin, TimestampMixin, coerce_aware, utc_now


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING_VERIFICATION = "pending_verification"


class User(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=Role.BUYER.value, index=True)
    status = db.Column(db.String(32), nullable=False, default=UserStatus.ACTIVE.value, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(40), nullable=True)

    sessions = db.relationship(
        "AuthSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    products = db.relationship("Product", back_populates="seller", lazy="selectin")
    wishlist_items = db.relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    carts = db.relationship("Cart", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    orders = db.relationship("Order", back_populates="user", lazy="selectin")
    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    product_reports = db.relationship(
        "ProductReport",
        foreign_keys="ProductReport.reporter_id",
        back_populates="reporter",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @validates("email")
    def validate_email(self, key, value):
        normalized = (value or "").strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("A valid email address is required.")
        return normalized

    @validates("role")
    def validate_role(self, key, value):
        if not is_valid_role(value):
            raise ValueError("User role is not supported.")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in UserStatus}:
            raise ValueError("User status is not supported.")
        return value

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    @property
    def is_active(self):
        return self.status == UserStatus.ACTIVE.value

    def to_public_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AuthSession(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "auth_sessions"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    user_agent = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="sessions")

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def from_token(cls, token, **kwargs):
        return cls(token_hash=cls.hash_token(token), **kwargs)

    @property
    def is_revoked(self):
        return self.revoked_at is not None

    @property
    def is_expired(self):
        return coerce_aware(self.expires_at) <= utc_now()

    @property
    def is_valid(self):
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        self.revoked_at = utc_now()
