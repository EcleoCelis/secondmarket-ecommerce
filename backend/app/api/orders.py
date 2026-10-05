from flask import Blueprint, g, request

from backend.app.auth.decorators import roles_required
from backend.app.auth.rbac import Role
from backend.app.core.responses import error_response, success_response
from backend.app.orders.serializers import serialize_order_detail, serialize_order_summary
from backend.app.orders.service import (
    cancel_buyer_order,
    get_admin_order_by_number,
    get_buyer_order_by_number,
    list_admin_orders,
    list_buyer_orders,
    parse_order_filters,
    update_admin_order_fulfillment,
)


orders_bp = Blueprint("orders", __name__, url_prefix="/orders")
admin_orders_bp = Blueprint("admin_orders", __name__, url_prefix="/admin/orders")


def order_filter_error_response(errors):
    return error_response(
        message="Request validation failed.",
        status_code=422,
        code="validation_error",
        details=errors,
    )


def order_not_found_response():
    return error_response(
        message="Order was not found.",
        status_code=404,
        code="order_not_found",
    )


def order_conflict_response(errors):
    return error_response(
        message="Order action is not allowed.",
        status_code=409,
        code="order_action_not_allowed",
        details=errors,
    )


@orders_bp.get("")
@roles_required(Role.BUYER.value)
def buyer_orders():
    filters, errors = parse_order_filters(request.args)
    if errors:
        return order_filter_error_response(errors)

    orders = list_buyer_orders(g.current_user, filters)
    return success_response(
        data=[serialize_order_summary(order) for order in orders],
        meta={"count": len(orders), "scope": "buyer"},
    )


@orders_bp.get("/<order_number>")
@roles_required(Role.BUYER.value)
def buyer_order_detail(order_number):
    order = get_buyer_order_by_number(g.current_user, order_number)
    if order is None:
        return order_not_found_response()

    return success_response(data=serialize_order_detail(order))


@orders_bp.patch("/<order_number>/cancel")
@roles_required(Role.BUYER.value)
def buyer_cancel_order(order_number):
    order = get_buyer_order_by_number(g.current_user, order_number)
    if order is None:
        return order_not_found_response()

    cancelled_order, errors = cancel_buyer_order(order)
    if errors:
        return order_conflict_response(errors)

    return success_response(
        data=serialize_order_detail(cancelled_order),
        message="Order cancelled.",
    )


@admin_orders_bp.get("")
@roles_required(Role.ADMIN.value)
def admin_orders():
    filters, errors = parse_order_filters(request.args)
    if errors:
        return order_filter_error_response(errors)

    orders = list_admin_orders(filters)
    return success_response(
        data=[serialize_order_summary(order, include_buyer=True) for order in orders],
        meta={"count": len(orders), "scope": "admin"},
    )


@admin_orders_bp.get("/<order_number>")
@roles_required(Role.ADMIN.value)
def admin_order_detail(order_number):
    order = get_admin_order_by_number(order_number)
    if order is None:
        return order_not_found_response()

    return success_response(data=serialize_order_detail(order, include_buyer=True))


@admin_orders_bp.patch("/<order_number>/fulfillment")
@roles_required(Role.ADMIN.value)
def admin_update_order_fulfillment(order_number):
    order = get_admin_order_by_number(order_number)
    if order is None:
        return order_not_found_response()

    updated_order, errors = update_admin_order_fulfillment(order, request.get_json(silent=True))
    if errors:
        return order_filter_error_response(errors)

    return success_response(
        data=serialize_order_detail(updated_order, include_buyer=True),
        message="Order fulfillment updated.",
    )
