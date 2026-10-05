import re
from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash


MIN_PASSWORD_LENGTH = 8


@dataclass(frozen=True)
class PasswordValidationResult:
    is_valid: bool
    errors: tuple[str, ...] = ()


def validate_password_strength(password):
    errors = []

    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must include at least one number.")

    return PasswordValidationResult(is_valid=not errors, errors=tuple(errors))


def hash_password(password):
    validation = validate_password_strength(password)
    if not validation.is_valid:
        raise ValueError("Password does not meet strength requirements.")

    return generate_password_hash(password)


def verify_password(password_hash, password):
    if not password_hash or not password:
        return False

    return check_password_hash(password_hash, password)
