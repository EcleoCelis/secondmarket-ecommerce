from backend.app.auth.validation import require_json_object


SUPPORTED_PAYMENT_METHODS = {"cash_on_delivery", "gcash_pending"}


def clean_text(value):
    return str(value or "").strip()


def validate_checkout_draft_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    shipping_payload = payload.get("shipping_address")
    if not isinstance(shipping_payload, dict):
        errors.setdefault("shipping_address", []).append("Shipping address is required.")
        shipping_payload = {}

    required_shipping_fields = (
        "recipient_name",
        "phone",
        "address_line1",
        "city",
        "province",
        "postal_code",
    )
    shipping_address = {}
    for field_name in required_shipping_fields:
        value = clean_text(shipping_payload.get(field_name))
        shipping_address[field_name] = value
        if not value:
            errors.setdefault(f"shipping_address.{field_name}", []).append(f"{field_name} is required.")

    shipping_address["address_line2"] = clean_text(shipping_payload.get("address_line2")) or None
    shipping_address["country"] = clean_text(shipping_payload.get("country")) or "Philippines"

    payment_method = clean_text(payload.get("payment_method"))
    if not payment_method:
        errors.setdefault("payment_method", []).append("Payment method is required.")
    elif payment_method not in SUPPORTED_PAYMENT_METHODS:
        errors.setdefault("payment_method", []).append("Payment method must be cash_on_delivery or gcash_pending.")

    return {
        "shipping_address": shipping_address,
        "payment_method": payment_method,
    }, errors
