from flask import Blueprint, g, request

from backend.app.admin.serializers import serialize_admin_category, serialize_admin_product
from backend.app.admin.service import (
    AdminCategoryError,
    AdminProductError,
    create_admin_category,
    create_admin_product,
    get_admin_product_by_slug,
    get_category_by_slug,
    list_admin_categories,
    list_admin_products,
    parse_admin_product_filters,
    update_admin_category,
    update_admin_category_status,
    update_admin_product,
    update_admin_product_quantity,
    update_admin_product_status,
)
from backend.app.admin.validation import (
    validate_category_payload,
    validate_category_status_payload,
    validate_product_inventory_payload,
    validate_product_payload,
    validate_product_status_payload,
)
from backend.app.auth.decorators import roles_required
from backend.app.auth.rbac import Role
from backend.app.core.responses import error_response, success_response


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def validation_error_response(errors):
    return error_response(
        message="Request validation failed.",
        status_code=422,
        code="validation_error",
        details=errors,
    )


def admin_product_error_response(error):
    return error_response(
        message=error.message,
        status_code=error.status_code,
        code=error.code,
        details=error.details,
    )


def admin_category_error_response(error):
    return error_response(
        message=error.message,
        status_code=error.status_code,
        code=error.code,
        details=error.details,
    )


@admin_bp.get("/categories")
@roles_required(Role.ADMIN.value)
def categories():
    return success_response(
        data=[
            serialize_admin_category(category, product_count=product_count)
            for category, product_count in list_admin_categories()
        ],
        meta={"scope": "admin"},
    )


@admin_bp.post("/categories")
@roles_required(Role.ADMIN.value)
def create_category():
    data, errors = validate_category_payload(request.get_json(silent=True), partial=False)
    if errors:
        return validation_error_response(errors)

    try:
        category = create_admin_category(data)
    except AdminCategoryError as error:
        return admin_category_error_response(error)

    return success_response(
        data=serialize_admin_category(category, product_count=0),
        message="Category created.",
        status_code=201,
    )


@admin_bp.put("/categories/<slug>")
@roles_required(Role.ADMIN.value)
def update_category(slug):
    category = get_category_by_slug(slug)
    if category is None:
        return error_response(
            message="Category was not found.",
            status_code=404,
            code="category_not_found",
        )

    data, errors = validate_category_payload(request.get_json(silent=True), partial=True)
    if errors:
        return validation_error_response(errors)

    try:
        category = update_admin_category(category, data)
    except AdminCategoryError as error:
        return admin_category_error_response(error)

    return success_response(
        data=serialize_admin_category(category, product_count=len(category.products)),
        message="Category updated.",
    )


@admin_bp.patch("/categories/<slug>/status")
@roles_required(Role.ADMIN.value)
def update_category_status(slug):
    category = get_category_by_slug(slug)
    if category is None:
        return error_response(
            message="Category was not found.",
            status_code=404,
            code="category_not_found",
        )

    data, errors = validate_category_status_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    category = update_admin_category_status(category, data["is_active"])
    return success_response(
        data=serialize_admin_category(category, product_count=len(category.products)),
        message="Category status updated.",
    )


@admin_bp.get("/products")
@roles_required(Role.ADMIN.value)
def products():
    filters, errors = parse_admin_product_filters(request.args)
    if errors:
        return error_response(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details=errors,
        )

    products = list_admin_products(filters)
    return success_response(
        data=[serialize_admin_product(product) for product in products],
        meta={"count": len(products), "scope": "admin"},
    )


@admin_bp.post("/products")
@roles_required(Role.ADMIN.value)
def create_product():
    data, errors = validate_product_payload(request.get_json(silent=True), partial=False)
    if errors:
        return validation_error_response(errors)

    try:
        product = create_admin_product(g.current_user, data)
    except AdminProductError as error:
        return admin_product_error_response(error)

    return success_response(
        data=serialize_admin_product(product),
        message="Product created.",
        status_code=201,
    )


@admin_bp.put("/products/<slug>")
@roles_required(Role.ADMIN.value)
def update_product(slug):
    product = get_admin_product_by_slug(slug)
    if product is None:
        return error_response(
            message="Product was not found.",
            status_code=404,
            code="product_not_found",
        )

    data, errors = validate_product_payload(request.get_json(silent=True), partial=True)
    if errors:
        return validation_error_response(errors)

    try:
        product = update_admin_product(product, data)
    except AdminProductError as error:
        return admin_product_error_response(error)

    return success_response(
        data=serialize_admin_product(product),
        message="Product updated.",
    )


@admin_bp.patch("/products/<slug>/status")
@roles_required(Role.ADMIN.value)
def update_product_status(slug):
    product = get_admin_product_by_slug(slug)
    if product is None:
        return error_response(
            message="Product was not found.",
            status_code=404,
            code="product_not_found",
        )

    data, errors = validate_product_status_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        product = update_admin_product_status(product, data["status"])
    except AdminProductError as error:
        return admin_product_error_response(error)

    return success_response(
        data=serialize_admin_product(product),
        message="Product status updated.",
    )


@admin_bp.patch("/products/<slug>/inventory")
@roles_required(Role.ADMIN.value)
def update_product_inventory(slug):
    product = get_admin_product_by_slug(slug)
    if product is None:
        return error_response(
            message="Product was not found.",
            status_code=404,
            code="product_not_found",
        )

    data, errors = validate_product_inventory_payload(request.get_json(silent=True))
    if errors:
        return validation_error_response(errors)

    try:
        product = update_admin_product_quantity(product, data["quantity"])
    except AdminProductError as error:
        return admin_product_error_response(error)

    return success_response(
        data=serialize_admin_product(product),
        message="Product inventory updated.",
    )
