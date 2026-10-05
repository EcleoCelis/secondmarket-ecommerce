import re

from backend.app.auth.validation import require_json_object
from backend.app.models import ProductCondition, ProductStatus


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRODUCT_CONDITIONS = {condition.value for condition in ProductCondition}
PRODUCT_STATUSES = {status.value for status in ProductStatus}


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return slug.strip("-")


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_nonnegative_integer(value, field_name, errors):
    if isinstance(value, bool):
        errors.setdefault(field_name, []).append(f"{field_name} must be a non-negative integer.")
        return None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.setdefault(field_name, []).append(f"{field_name} must be a non-negative integer.")
        return None

    if parsed < 0:
        errors.setdefault(field_name, []).append(f"{field_name} cannot be negative.")
        return None

    return parsed


def validate_images_payload(images):
    errors = {}
    normalized = []

    if images is None:
        return None, errors

    if not isinstance(images, list):
        return None, {"images": ["Images must be a list."]}

    primary_count = 0
    for index, image in enumerate(images):
        field_prefix = f"images.{index}"
        if not isinstance(image, dict):
            errors.setdefault(field_prefix, []).append("Image must be an object.")
            continue

        image_url = clean_text(image.get("image_url") or image.get("url"))
        alt_text = clean_text(image.get("alt_text"))
        sort_order = parse_nonnegative_integer(image.get("sort_order", index), f"{field_prefix}.sort_order", errors)
        is_primary = bool(image.get("is_primary", False))

        if not image_url:
            errors.setdefault(f"{field_prefix}.image_url", []).append("Image URL is required.")
        if not alt_text:
            errors.setdefault(f"{field_prefix}.alt_text", []).append("Alt text is required.")
        if is_primary:
            primary_count += 1

        normalized.append(
            {
                "image_url": image_url,
                "alt_text": alt_text,
                "sort_order": sort_order if sort_order is not None else index,
                "is_primary": is_primary,
            }
        )

    if primary_count > 1:
        errors.setdefault("images", []).append("Only one image can be marked as primary.")

    return normalized, errors


def validate_product_payload(payload, partial=False):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    data = {}
    required_fields = ("title", "category_slug", "description", "price_cents", "condition", "quantity")
    editable_text_fields = ("title", "slug", "category_slug", "description", "brand", "color", "material", "dimensions")

    for field_name in editable_text_fields:
        if field_name in payload:
            data[field_name] = clean_text(payload.get(field_name))

    if not partial:
        for field_name in required_fields:
            if field_name not in payload or clean_text(payload.get(field_name)) == "":
                errors.setdefault(field_name, []).append(f"{field_name} is required.")

    if "title" in data and not data["title"]:
        errors.setdefault("title", []).append("Title is required.")

    if "description" in data and not data["description"]:
        errors.setdefault("description", []).append("Description is required.")

    if "category_slug" in data and not data["category_slug"]:
        errors.setdefault("category_slug", []).append("Category is required.")

    if not partial and "slug" not in data and data.get("title"):
        data["slug"] = slugify(data["title"])

    if "slug" in data:
        if not data["slug"] and data.get("title"):
            data["slug"] = slugify(data["title"])
        if not data["slug"]:
            errors.setdefault("slug", []).append("Slug is required.")
        elif not SLUG_PATTERN.match(data["slug"]):
            errors.setdefault("slug", []).append("Slug must contain lowercase letters, numbers, and hyphens only.")

    if "price_cents" in payload:
        data["price_cents"] = parse_nonnegative_integer(payload.get("price_cents"), "price_cents", errors)

    if "quantity" in payload:
        data["quantity"] = parse_nonnegative_integer(payload.get("quantity"), "quantity", errors)

    if "condition" in payload:
        condition = clean_text(payload.get("condition"))
        data["condition"] = condition
        if condition not in PRODUCT_CONDITIONS:
            errors.setdefault("condition", []).append("Condition must be new_other, like_new, good, fair, or for_repair.")

    if "status" in payload:
        status = clean_text(payload.get("status")) or ProductStatus.DRAFT.value
        data["status"] = status
        if status not in PRODUCT_STATUSES:
            errors.setdefault("status", []).append("Status must be draft, available, reserved, sold, or hidden.")
    elif not partial:
        data["status"] = ProductStatus.DRAFT.value

    if data.get("status") == ProductStatus.AVAILABLE.value and data.get("quantity") == 0:
        errors.setdefault("quantity", []).append("Available products must have at least one item in stock.")

    if "images" in payload:
        images, image_errors = validate_images_payload(payload.get("images"))
        data["images"] = images
        errors.update(image_errors)

    if partial and not data:
        errors.setdefault("body", []).append("At least one product field is required.")

    return data, errors


def validate_product_status_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    status = clean_text(payload.get("status"))
    if not status:
        errors.setdefault("status", []).append("Status is required.")
    elif status not in PRODUCT_STATUSES:
        errors.setdefault("status", []).append("Status must be draft, available, reserved, sold, or hidden.")

    return {"status": status}, errors


def validate_product_inventory_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    if "quantity" not in payload:
        errors.setdefault("quantity", []).append("Quantity is required.")
        return {}, errors

    quantity = parse_nonnegative_integer(payload.get("quantity"), "quantity", errors)
    return {"quantity": quantity}, errors


def parse_boolean(value, field_name, errors):
    if isinstance(value, bool):
        return value

    errors.setdefault(field_name, []).append(f"{field_name} must be true or false.")
    return None


def validate_category_payload(payload, partial=False):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    data = {}
    for field_name in ("name", "slug", "description"):
        if field_name in payload:
            data[field_name] = clean_text(payload.get(field_name))

    if not partial and "name" not in payload:
        errors.setdefault("name", []).append("Name is required.")

    if "name" in data and not data["name"]:
        errors.setdefault("name", []).append("Name is required.")

    if not partial and "slug" not in data and data.get("name"):
        data["slug"] = slugify(data["name"])

    if "slug" in data:
        if not data["slug"] and data.get("name"):
            data["slug"] = slugify(data["name"])
        if not data["slug"]:
            errors.setdefault("slug", []).append("Slug is required.")
        elif not SLUG_PATTERN.match(data["slug"]):
            errors.setdefault("slug", []).append("Slug must contain lowercase letters, numbers, and hyphens only.")

    if "sort_order" in payload:
        data["sort_order"] = parse_nonnegative_integer(payload.get("sort_order"), "sort_order", errors)
    elif not partial:
        data["sort_order"] = 0

    if "is_active" in payload:
        data["is_active"] = parse_boolean(payload.get("is_active"), "is_active", errors)
    elif not partial:
        data["is_active"] = True

    if partial and not data:
        errors.setdefault("body", []).append("At least one category field is required.")

    return data, errors


def validate_category_status_payload(payload):
    payload, errors = require_json_object(payload)
    if errors:
        return {}, errors

    if "is_active" not in payload:
        errors.setdefault("is_active", []).append("is_active is required.")
        return {}, errors

    is_active = parse_boolean(payload.get("is_active"), "is_active", errors)
    return {"is_active": is_active}, errors
