from enum import StrEnum


class Role(StrEnum):
    BUYER = "buyer"
    ADMIN = "admin"


PUBLIC_ROLES = tuple(role.value for role in Role)


def is_valid_role(role):
    return role in PUBLIC_ROLES
