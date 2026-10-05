from flask import Blueprint, g, request

from backend.app.auth.decorators import roles_required
from backend.app.auth.rbac import Role
from backend.app.cart.serializers import serialize_cart
from backend.app.cart.service import (
    CartError,
    add_cart_item,
    get_or_create_active_cart,
    remove_cart_item,
    update_cart_item_quantity,
)
from backend.app.cart.validation import validate_add_cart_item_payload, validate_update_cart_item_payload
from backend.app.core.responses import error_response, success_response


cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


def validation_error_response(errors):
    return error_response(
        message="Request validation failed.",
        status_code=422,
        code="validation_error",
        details=errors,
    )


def cart_error_response(error):
    return error_response(
        message=error.message,
        status_code=error.status_code,
        code=error.code,
        details=error.details,
    )


@cart_bp.get("")
@roles_required(Role.BUYER.value)
def current_cart():
    cart = get_or_create_active_cart(g.current_user)
    return success_response(data=serialize_cart(cart))


@cart_bp.post("/items")
@roles_required(Role.BUYER.value)
def add_item():
    data, errors = validate_add_cart_item_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        cart = add_cart_item(g.current_user, data["product_slug"], data["quantity"])
    except CartError as error:
        return cart_error_response(error)

    return success_response(
        data=serialize_cart(cart),
        message="Product added to cart.",
        status_code=201,
    )


@cart_bp.patch("/items/<slug>")
@roles_required(Role.BUYER.value)
def update_item(slug):
    data, errors = validate_update_cart_item_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        cart = update_cart_item_quantity(g.current_user, slug, data["quantity"])
    except CartError as error:
        return cart_error_response(error)

    return success_response(
        data=serialize_cart(cart),
        message="Cart item updated.",
    )


@cart_bp.delete("/items/<slug>")
@roles_required(Role.BUYER.value)
def remove_item(slug):
    try:
        cart = remove_cart_item(g.current_user, slug)
    except CartError as error:
        return cart_error_response(error)

    return success_response(
        data=serialize_cart(cart),
        message="Product removed from cart.",
    )
