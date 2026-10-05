from flask import Blueprint, g, request

from backend.app.auth.decorators import roles_required
from backend.app.auth.rbac import Role
from backend.app.checkout.serializers import serialize_checkout_draft, serialize_order_confirmation
from backend.app.checkout.service import CheckoutError, build_checkout_draft, place_checkout_order
from backend.app.checkout.validation import validate_checkout_draft_payload
from backend.app.core.responses import error_response, success_response


checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


def validation_error_response(errors):
    return error_response(
        message="Request validation failed.",
        status_code=422,
        code="validation_error",
        details=errors,
    )


def checkout_error_response(error):
    return error_response(
        message=error.message,
        status_code=error.status_code,
        code=error.code,
        details=error.details,
    )


@checkout_bp.post("/draft")
@roles_required(Role.BUYER.value)
def create_checkout_draft():
    data, errors = validate_checkout_draft_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        draft = build_checkout_draft(g.current_user, data)
    except CheckoutError as error:
        return checkout_error_response(error)

    return success_response(
        data=serialize_checkout_draft(draft),
        message="Checkout draft validated.",
    )


@checkout_bp.post("/confirm")
@roles_required(Role.BUYER.value)
def confirm_checkout():
    data, errors = validate_checkout_draft_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        order = place_checkout_order(g.current_user, data)
    except CheckoutError as error:
        return checkout_error_response(error)

    return success_response(
        data=serialize_order_confirmation(order),
        message="Order placed successfully.",
        status_code=201,
    )
