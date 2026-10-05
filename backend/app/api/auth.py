from flask import Blueprint, current_app, request

from backend.app.auth.service import (
    AuthError,
    authenticate_user,
    create_auth_session,
    find_session_by_token,
    register_buyer,
    revoke_session,
)
from backend.app.auth.validation import validate_login_payload, validate_register_payload
from backend.app.core.responses import error_response, success_response


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def validation_error_response(errors):
    return error_response(
        message="Request validation failed.",
        status_code=422,
        code="validation_error",
        details=errors,
    )


def not_implemented_response(next_step):
    return error_response(
        message="Authentication persistence is not wired yet.",
        status_code=501,
        code="auth_workflow_not_implemented",
        details={"next_step": next_step},
    )


def auth_error_response(error):
    return error_response(
        message=error.message,
        status_code=error.status_code,
        code=error.code,
        details=error.details,
    )


def session_cookie_name():
    return current_app.config["AUTH_SESSION_COOKIE_NAME"]


def get_current_session():
    token = request.cookies.get(session_cookie_name())
    return find_session_by_token(token)


def attach_session_cookie(response, token, session):
    response.set_cookie(
        session_cookie_name(),
        token,
        httponly=True,
        secure=not current_app.config["DEBUG"] and not current_app.config["TESTING"],
        samesite="Lax",
        expires=session.expires_at,
        path="/",
    )
    return response


@auth_bp.post("/register")
def register():
    data, errors = validate_register_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        user = register_buyer(data)
        token, session = create_auth_session(
            user,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.remote_addr,
            duration_days=current_app.config["AUTH_SESSION_DAYS"],
        )
    except AuthError as error:
        return auth_error_response(error)

    response, status_code = success_response(
        data={"authenticated": True, "user": user.to_public_dict()},
        message="Registration successful.",
        status_code=201,
    )
    attach_session_cookie(response, token, session)
    return response, status_code


@auth_bp.post("/login")
def login():
    data, errors = validate_login_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        user = authenticate_user(data["email"], data["password"])
        token, session = create_auth_session(
            user,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.remote_addr,
            duration_days=current_app.config["AUTH_SESSION_DAYS"],
        )
    except AuthError as error:
        return auth_error_response(error)

    response, status_code = success_response(
        data={"authenticated": True, "user": user.to_public_dict()},
        message="Login successful.",
    )
    attach_session_cookie(response, token, session)
    return response, status_code


@auth_bp.post("/logout")
def logout():
    session = get_current_session()
    if session is not None:
        revoke_session(session)

    response, status_code = success_response(data={"authenticated": False}, message="Logout successful.")
    response.delete_cookie(session_cookie_name(), path="/")
    return response, status_code


@auth_bp.get("/me")
def current_user():
    session = get_current_session()
    if session is not None:
        return success_response(
            data={"authenticated": True, "user": session.user.to_public_dict()},
            message="Authenticated user loaded.",
        )

    return success_response(
        data={"authenticated": False, "user": None},
        message="No authenticated user is available.",
    )
