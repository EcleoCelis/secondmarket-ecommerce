import pytest

from backend.app.auth.rbac import PUBLIC_ROLES, Role, is_valid_role
from backend.app.auth.security import hash_password, validate_password_strength, verify_password


def test_supported_roles_are_buyer_and_admin():
    assert Role.BUYER.value == "buyer"
    assert Role.ADMIN.value == "admin"
    assert PUBLIC_ROLES == ("buyer", "admin")


def test_role_validation_rejects_unknown_roles():
    assert is_valid_role("buyer") is True
    assert is_valid_role("admin") is True
    assert is_valid_role("seller") is False
    assert is_valid_role("") is False


def test_password_strength_requires_length_case_and_number():
    result = validate_password_strength("weak")

    assert result.is_valid is False
    assert "Password must be at least 8 characters long." in result.errors
    assert "Password must include at least one uppercase letter." in result.errors
    assert "Password must include at least one number." in result.errors


def test_password_strength_accepts_valid_password():
    result = validate_password_strength("Secondhand2026")

    assert result.is_valid is True
    assert result.errors == ()


def test_password_hash_is_not_plain_text_and_can_be_verified():
    password_hash = hash_password("Secondhand2026")

    assert password_hash != "Secondhand2026"
    assert verify_password(password_hash, "Secondhand2026") is True
    assert verify_password(password_hash, "WrongPassword2026") is False


def test_hash_password_rejects_weak_passwords():
    with pytest.raises(ValueError):
        hash_password("weak")
