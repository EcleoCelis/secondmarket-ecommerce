from backend.app.auth.validation import require_json_object


def parse_positive_integer(value, field_name, errors):
    if isinstance(value, bool):
        errors.setdefault(field_name, []).append(f"{field_name} must be a positive integer.")
        return None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.setdefault(field_name, []).append(f"{field_name} must be a positive integer.")
        return None

    if parsed < 1:
        errors.setdefault(field_name, []).append(f"{field_name} must be at least 1.")
        return None

    return parsed


def validate_add_cart_item_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    product_slug = str(payload.get("product_slug") or "").strip()
    if not product_slug:
        errors.setdefault("product_slug", []).append("Product slug is required.")

    quantity = parse_positive_integer(payload.get("quantity", 1), "quantity", errors)
    return {"product_slug": product_slug, "quantity": quantity}, errors


def validate_update_cart_item_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    if "quantity" not in payload:
        errors.setdefault("quantity", []).append("Quantity is required.")
        return {}, errors

    quantity = parse_positive_integer(payload.get("quantity"), "quantity", errors)
    return {"quantity": quantity}, errors
