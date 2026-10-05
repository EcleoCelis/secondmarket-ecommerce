import secrets
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from backend.app.auth.rbac import Role
from backend.app.extensions import db
from backend.app.models import AuthSession, User, UserStatus
from backend.app.models.base import utc_now


class AuthError(Exception):
    def __init__(self, message, code="auth_error", status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


def register_buyer(data):
    if data["role"] != Role.BUYER.value:
        raise AuthError(
            "Only buyer registration is available publicly.",
            code="role_not_allowed",
            status_code=403,
            details={"role": ["Admin accounts must be created through an administrative workflow."]},
        )

    user = User(
        email=data["email"],
        role=Role.BUYER.value,
        status=UserStatus.ACTIVE.value,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
    )
    user.set_password(data["password"])

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthError(
            "An account with this email already exists.",
            code="email_already_registered",
            status_code=409,
            details={"email": ["An account with this email already exists."]},
        ) from exc

    return user


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).one_or_none()
    if user is None or not user.check_password(password):
        raise AuthError("Invalid email or password.", code="invalid_credentials", status_code=401)

    if not user.is_active:
        raise AuthError("This account is not active.", code="account_not_active", status_code=403)

    return user


def create_auth_session(user, *, user_agent=None, ip_address=None, duration_days=7):
    token = secrets.token_urlsafe(48)
    session = AuthSession.from_token(
        token,
        user=user,
        user_agent=(user_agent or "")[:255] or None,
        ip_address=ip_address,
        expires_at=utc_now() + timedelta(days=duration_days),
    )
    db.session.add(session)
    db.session.commit()
    return token, session


def find_session_by_token(token):
    if not token:
        return None

    token_hash = AuthSession.hash_token(token)
    session = AuthSession.query.filter_by(token_hash=token_hash).one_or_none()
    if session is None or not session.is_valid or not session.user.is_active:
        return None

    return session


def revoke_session(session):
    session.revoke()
    db.session.commit()
