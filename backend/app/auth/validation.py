from backend.app.auth.rbac import Role, is_valid_role
from backend.app.auth.security import validate_password_strength
from backend.app.models.identity import EMAIL_PATTERN


def require_json_object(payload):
    if not isinstance(payload, dict):
        return {}, {"body": ["Request body must be a JSON object."]}

    return payload, {}


def validate_register_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    role = (payload.get("role") or Role.BUYER.value).strip()
    phone = (payload.get("phone") or "").strip() or None
    errors = {}

    if not EMAIL_PATTERN.match(email):
        errors.setdefault("email", []).append("A valid email address is required.")

    password_result = validate_password_strength(password)
    if not password_result.is_valid:
        errors["password"] = list(password_result.errors)

    if not first_name:
        errors.setdefault("first_name", []).append("First name is required.")
    if not last_name:
        errors.setdefault("last_name", []).append("Last name is required.")
    if not is_valid_role(role):
        errors.setdefault("role", []).append("Role must be buyer or admin.")
    elif role != Role.BUYER.value:
        errors.setdefault("role", []).append("Only buyer registration is available publicly.")

    data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "phone": phone,
    }
    return data, errors


def validate_login_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    errors = {}

    if not EMAIL_PATTERN.match(email):
        errors.setdefault("email", []).append("A valid email address is required.")
    if not password:
        errors.setdefault("password", []).append("Password is required.")

    return {"email": email, "password": password}, errors
