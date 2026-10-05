from datetime import datetime, timezone

from backend.app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


def coerce_aware(value):
    if value is None or value.tzinfo is not None:
        return value

    return value.replace(tzinfo=timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class IntPrimaryKeyMixin:
    id = db.Column(db.Integer, primary_key=True)
