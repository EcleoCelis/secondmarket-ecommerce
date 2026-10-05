from functools import wraps

from flask import current_app, g, request

from backend.app.auth.service import find_session_by_token
from backend.app.core.responses import error_response


def load_current_session():
    token = request.cookies.get(current_app.config["AUTH_SESSION_COOKIE_NAME"])
    session = find_session_by_token(token)
    g.current_session = session
    g.current_user = session.user if session is not None else None
    return session


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if load_current_session() is None:
            return error_response(
                message="Authentication is required.",
                status_code=401,
                code="authentication_required",
            )

        return view(*args, **kwargs)

    return wrapped


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            session = load_current_session()
            if session is None:
                return error_response(
                    message="Authentication is required.",
                    status_code=401,
                    code="authentication_required",
                )

            if session.user.role not in allowed_roles:
                return error_response(
                    message="You do not have permission to access this resource.",
                    status_code=403,
                    code="permission_denied",
                    details={"required_roles": list(allowed_roles)},
                )

            return view(*args, **kwargs)

        return wrapped

    return decorator
