from backend.app.models import OrderStatus, PaymentStatus, ShippingStatus


ORDER_STATUS_VALUES = {status.value for status in OrderStatus}
PAYMENT_STATUS_VALUES = {status.value for status in PaymentStatus}
SHIPPING_STATUS_VALUES = {status.value for status in ShippingStatus}

ALLOWED_ORDER_TRANSITIONS = {
    OrderStatus.PENDING.value: {OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value},
    OrderStatus.CONFIRMED.value: {OrderStatus.PROCESSING.value, OrderStatus.CANCELLED.value},
    OrderStatus.PROCESSING.value: {OrderStatus.SHIPPED.value, OrderStatus.CANCELLED.value},
    OrderStatus.SHIPPED.value: {OrderStatus.DELIVERED.value},
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}

ALLOWED_PAYMENT_TRANSITIONS = {
    PaymentStatus.PENDING.value: {PaymentStatus.PAID.value, PaymentStatus.FAILED.value},
    PaymentStatus.FAILED.value: {PaymentStatus.PENDING.value},
    PaymentStatus.PAID.value: {PaymentStatus.REFUNDED.value},
    PaymentStatus.REFUNDED.value: set(),
}

ALLOWED_SHIPPING_TRANSITIONS = {
    ShippingStatus.NOT_READY.value: {ShippingStatus.READY.value, ShippingStatus.SHIPPED.value, ShippingStatus.RETURNED.value},
    ShippingStatus.READY.value: {ShippingStatus.SHIPPED.value, ShippingStatus.RETURNED.value},
    ShippingStatus.SHIPPED.value: {ShippingStatus.DELIVERED.value, ShippingStatus.RETURNED.value},
    ShippingStatus.DELIVERED.value: set(),
    ShippingStatus.RETURNED.value: set(),
}

FULFILLMENT_FIELDS = {"order_status", "payment_status", "shipping_status", "tracking_number"}
CANCELLABLE_ORDER_STATUSES = {OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value}
CANCELLABLE_SHIPPING_STATUS = ShippingStatus.NOT_READY.value


def clean_optional_text(value):
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def transition_allowed(current_status, next_status, allowed_transitions):
    if current_status == next_status:
        return True
    return next_status in allowed_transitions.get(current_status, set())


def validate_status_transition(field, current_status, next_status, valid_values, allowed_transitions, errors):
    if next_status is None:
        return

    if next_status not in valid_values:
        errors.setdefault(field, []).append("Status is not supported.")
        return

    if not transition_allowed(current_status, next_status, allowed_transitions):
        errors.setdefault(field, []).append(f"Cannot change from {current_status} to {next_status}.")


def validate_fulfillment_payload(payload, order):
    if not isinstance(payload, dict):
        return {}, {"payload": ["JSON body is required."]}

    errors = {}
    unexpected_fields = sorted(set(payload) - FULFILLMENT_FIELDS)
    if unexpected_fields:
        errors.setdefault("payload", []).append(f"Unsupported field(s): {', '.join(unexpected_fields)}.")

    cleaned = {
        "order_status": clean_optional_text(payload.get("order_status")),
        "payment_status": clean_optional_text(payload.get("payment_status")),
        "shipping_status": clean_optional_text(payload.get("shipping_status")),
        "tracking_number": clean_optional_text(payload.get("tracking_number")),
    }

    if not any(value is not None for value in cleaned.values()):
        errors.setdefault("payload", []).append("At least one fulfillment field is required.")

    validate_status_transition(
        "order_status",
        order.status,
        cleaned["order_status"],
        ORDER_STATUS_VALUES,
        ALLOWED_ORDER_TRANSITIONS,
        errors,
    )
    validate_status_transition(
        "payment_status",
        order.payment_status,
        cleaned["payment_status"],
        PAYMENT_STATUS_VALUES,
        ALLOWED_PAYMENT_TRANSITIONS,
        errors,
    )
    validate_status_transition(
        "shipping_status",
        order.shipping_status,
        cleaned["shipping_status"],
        SHIPPING_STATUS_VALUES,
        ALLOWED_SHIPPING_TRANSITIONS,
        errors,
    )

    if cleaned["tracking_number"] and len(cleaned["tracking_number"]) > 120:
        errors.setdefault("tracking_number", []).append("Tracking number must be 120 characters or fewer.")

    next_shipping_status = cleaned["shipping_status"] or order.shipping_status
    next_tracking_number = cleaned["tracking_number"] or getattr(order.shipping_record, "tracking_number", None)
    if next_shipping_status in {ShippingStatus.SHIPPED.value, ShippingStatus.DELIVERED.value} and not next_tracking_number:
        errors.setdefault("tracking_number", []).append("Tracking number is required before marking an order shipped or delivered.")

    return cleaned, errors


def validate_buyer_cancellation(order):
    errors = {}

    if order.status not in CANCELLABLE_ORDER_STATUSES:
        errors.setdefault("order_status", []).append("This order can no longer be cancelled by the buyer.")

    if order.shipping_status != CANCELLABLE_SHIPPING_STATUS:
        errors.setdefault("shipping_status", []).append("Orders can only be cancelled before fulfillment begins.")

    return errors
