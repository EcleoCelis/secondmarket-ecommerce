from sqlalchemy.orm import selectinload

from backend.app.extensions import db
from backend.app.models import Order, OrderStatus, PaymentStatus, ProductStatus, ShippingStatus
from backend.app.orders.validation import validate_buyer_cancellation, validate_fulfillment_payload


ORDER_STATUSES = {status.value for status in OrderStatus}
PAYMENT_STATUSES = {status.value for status in PaymentStatus}
SHIPPING_STATUSES = {status.value for status in ShippingStatus}
ORDER_SORTS = {"recent", "oldest", "total_desc", "total_asc"}


def order_query():
    return Order.query.options(
        selectinload(Order.user),
        selectinload(Order.items),
        selectinload(Order.payments),
        selectinload(Order.shipping_record),
    )


def apply_order_filters(query, filters):
    if filters.get("status"):
        query = query.filter(Order.status == filters["status"])

    if filters.get("payment_status"):
        query = query.filter(Order.payment_status == filters["payment_status"])

    if filters.get("shipping_status"):
        query = query.filter(Order.shipping_status == filters["shipping_status"])

    sort = filters.get("sort") or "recent"
    if sort == "oldest":
        query = query.order_by(Order.placed_at.asc(), Order.id.asc())
    elif sort == "total_desc":
        query = query.order_by(Order.total_cents.desc(), Order.id.desc())
    elif sort == "total_asc":
        query = query.order_by(Order.total_cents.asc(), Order.id.desc())
    else:
        query = query.order_by(Order.placed_at.desc(), Order.id.desc())

    return query


def parse_order_filters(args):
    filters = {
        "status": (args.get("status") or "").strip(),
        "payment_status": (args.get("payment_status") or "").strip(),
        "shipping_status": (args.get("shipping_status") or "").strip(),
        "sort": (args.get("sort") or "recent").strip(),
    }
    errors = {}

    if filters["status"] and filters["status"] not in ORDER_STATUSES:
        errors.setdefault("status", []).append("Status is not supported.")

    if filters["payment_status"] and filters["payment_status"] not in PAYMENT_STATUSES:
        errors.setdefault("payment_status", []).append("Payment status is not supported.")

    if filters["shipping_status"] and filters["shipping_status"] not in SHIPPING_STATUSES:
        errors.setdefault("shipping_status", []).append("Shipping status is not supported.")

    if filters["sort"] not in ORDER_SORTS:
        errors.setdefault("sort", []).append("Sort must be recent, oldest, total_desc, or total_asc.")

    return filters, errors


def list_buyer_orders(user, filters):
    query = order_query().filter(Order.user_id == user.id)
    return apply_order_filters(query, filters).all()


def get_buyer_order_by_number(user, order_number):
    return order_query().filter(Order.user_id == user.id, Order.order_number == order_number).one_or_none()


def list_admin_orders(filters):
    return apply_order_filters(order_query(), filters).all()


def get_admin_order_by_number(order_number):
    return order_query().filter(Order.order_number == order_number).one_or_none()


def update_admin_order_fulfillment(order, payload):
    cleaned, errors = validate_fulfillment_payload(payload, order)
    if errors:
        return None, errors

    if cleaned["order_status"]:
        order.status = cleaned["order_status"]

    if cleaned["payment_status"]:
        order.payment_status = cleaned["payment_status"]
        for payment in order.payments:
            payment.status = cleaned["payment_status"]

    if cleaned["shipping_status"]:
        order.shipping_status = cleaned["shipping_status"]
        if order.shipping_record:
            order.shipping_record.status = cleaned["shipping_status"]

    if cleaned["tracking_number"] and order.shipping_record:
        order.shipping_record.tracking_number = cleaned["tracking_number"]

    db.session.commit()
    return order, {}


def cancel_buyer_order(order):
    errors = validate_buyer_cancellation(order)
    if errors:
        return None, errors

    order.status = OrderStatus.CANCELLED.value

    if order.payment_status == PaymentStatus.PAID.value:
        order.payment_status = PaymentStatus.REFUNDED.value
        for payment in order.payments:
            if payment.status == PaymentStatus.PAID.value:
                payment.status = PaymentStatus.REFUNDED.value

    for item in order.items:
        if item.product is None:
            continue

        item.product.quantity += item.quantity
        if item.product.status == ProductStatus.SOLD.value and item.product.quantity > 0:
            item.product.status = ProductStatus.AVAILABLE.value

    db.session.commit()
    return order, {}
