from enum import StrEnum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates

from backend.app.extensions import db
from backend.app.models.base import IntPrimaryKeyMixin, TimestampMixin, utc_now


class ReviewStatus(StrEnum):
    PUBLISHED = "published"
    HIDDEN = "hidden"
    FLAGGED = "flagged"


class ReportReason(StrEnum):
    MISLEADING = "misleading"
    INAPPROPRIATE = "inappropriate"
    COUNTERFEIT = "counterfeit"
    WRONG_CATEGORY = "wrong_category"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Review(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        UniqueConstraint("user_id", "product_id", "order_id", name="uq_reviews_user_product_order"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(140), nullable=True)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default=ReviewStatus.PUBLISHED.value, index=True)

    user = db.relationship("User", back_populates="reviews")
    product = db.relationship("Product", back_populates="reviews")
    order = db.relationship("Order", back_populates="reviews")

    @validates("rating")
    def validate_rating(self, key, value):
        if value < 1 or value > 5:
            raise ValueError("Review rating must be between 1 and 5.")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in ReviewStatus}:
            raise ValueError("Review status is not supported.")
        return value


class ProductReport(IntPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "product_reports"

    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = db.Column(db.String(40), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default=ReportStatus.OPEN.value, index=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    product = db.relationship("Product", back_populates="reports")
    reporter = db.relationship("User", foreign_keys=[reporter_id], back_populates="product_reports")
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])

    @validates("reason")
    def validate_reason(self, key, value):
        if value not in {reason.value for reason in ReportReason}:
            raise ValueError("Product report reason is not supported.")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if value not in {status.value for status in ReportStatus}:
            raise ValueError("Product report status is not supported.")
        return value

    def resolve(self, admin_user, status=ReportStatus.RESOLVED.value):
        if status not in {ReportStatus.RESOLVED.value, ReportStatus.DISMISSED.value}:
            raise ValueError("Report can only be resolved or dismissed.")

        self.status = status
        self.resolved_by = admin_user
        self.resolved_at = utc_now()
