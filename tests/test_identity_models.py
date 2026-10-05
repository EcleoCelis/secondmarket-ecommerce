from datetime import timedelta

import pytest

from backend.app import create_app
from backend.app.auth.rbac import Role
from backend.app.core.config import TestingConfig
from backend.app.extensions import db
from backend.app.models import AuthSession, User, UserStatus
from backend.app.models.base import utc_now


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_identity_tables_are_registered(app):
    assert "users" in db.metadata.tables
    assert "auth_sessions" in db.metadata.tables


def test_user_email_is_normalized_and_password_is_hashed(app):
    user = User(
        email=" Buyer@Example.COM ",
        role=Role.BUYER.value,
        first_name="Second",
        last_name="Buyer",
    )
    user.set_password("Secondhand2026")

    db.session.add(user)
    db.session.commit()

    assert user.email == "buyer@example.com"
    assert user.password_hash != "Secondhand2026"
    assert user.check_password("Secondhand2026") is True
    assert user.check_password("WrongPassword2026") is False
    assert user.is_active is True


def test_user_rejects_invalid_email_role_and_status(app):
    with pytest.raises(ValueError):
        User(email="invalid", role=Role.BUYER.value, first_name="Bad", last_name="Email")

    with pytest.raises(ValueError):
        User(email="buyer@example.com", role="seller", first_name="Bad", last_name="Role")

    with pytest.raises(ValueError):
        User(
            email="buyer@example.com",
            role=Role.BUYER.value,
            status="unknown",
            first_name="Bad",
            last_name="Status",
        )


def test_admin_user_can_be_identified_by_role(app):
    admin = User(
        email="admin@example.com",
        role=Role.ADMIN.value,
        first_name="Admin",
        last_name="Seller",
    )
    admin.set_password("AdminSeller2026")

    db.session.add(admin)
    db.session.commit()

    assert admin.has_role(Role.ADMIN.value) is True
    assert admin.has_role(Role.BUYER.value) is False


def test_auth_session_hashes_token_and_tracks_validity(app):
    user = User(
        email="buyer@example.com",
        role=Role.BUYER.value,
        first_name="Second",
        last_name="Buyer",
    )
    user.set_password("Secondhand2026")
    session = AuthSession.from_token(
        "plain-session-token",
        user=user,
        user_agent="pytest",
        ip_address="127.0.0.1",
        expires_at=utc_now() + timedelta(hours=1),
    )

    db.session.add(user)
    db.session.add(session)
    db.session.commit()

    assert session.token_hash != "plain-session-token"
    assert len(session.token_hash) == 64
    assert session.is_valid is True

    session.revoke()

    assert session.is_revoked is True
    assert session.is_valid is False


def test_auth_session_expiry_is_detected(app):
    user = User(
        email="buyer@example.com",
        role=Role.BUYER.value,
        first_name="Second",
        last_name="Buyer",
        status=UserStatus.ACTIVE.value,
    )
    user.set_password("Secondhand2026")
    session = AuthSession.from_token(
        "expired-token",
        user=user,
        expires_at=utc_now() - timedelta(minutes=1),
    )

    db.session.add(user)
    db.session.add(session)
    db.session.commit()

    assert session.is_expired is True
    assert session.is_valid is False
