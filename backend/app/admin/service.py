from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from backend.app.extensions import db
from backend.app.models import Category, Product, ProductCondition, ProductImage, ProductStatus


ADMIN_PRODUCT_SORTS = {"recent", "title_asc", "price_asc", "price_desc", "quantity_asc", "quantity_desc"}
ADMIN_PRODUCT_STATUSES = {status.value for status in ProductStatus}
ADMIN_PRODUCT_CONDITIONS = {condition.value for condition in ProductCondition}


class AdminProductError(Exception):
    def __init__(self, message, status_code=400, code="admin_product_error", details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class AdminCategoryError(Exception):
    def __init__(self, message, status_code=400, code="admin_category_error", details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


def list_admin_categories():
    product_counts = dict(
        db.session.query(Product.category_id, func.count(Product.id))
        .group_by(Product.category_id)
        .all()
    )

    categories = Category.query.order_by(Category.sort_order.asc(), Category.name.asc()).all()
    return [(category, product_counts.get(category.id, 0)) for category in categories]


def admin_products_query():
    return Product.query.options(
        selectinload(Product.category),
        selectinload(Product.images),
        selectinload(Product.seller),
    ).join(Category)


def get_category_by_slug(slug):
    return Category.query.filter_by(slug=slug).one_or_none()


def category_slug_exists(slug, excluded_category_id=None):
    query = Category.query.filter(Category.slug == slug)
    if excluded_category_id is not None:
        query = query.filter(Category.id != excluded_category_id)
    return db.session.query(query.exists()).scalar()


def category_name_exists(name, excluded_category_id=None):
    query = Category.query.filter(func.lower(Category.name) == name.lower())
    if excluded_category_id is not None:
        query = query.filter(Category.id != excluded_category_id)
    return db.session.query(query.exists()).scalar()


def ensure_category_can_use_payload(data, category=None):
    excluded_category_id = category.id if category is not None else None

    if data.get("slug") and category_slug_exists(data["slug"], excluded_category_id=excluded_category_id):
        raise AdminCategoryError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"slug": ["Slug is already used by another category."]},
        )

    if data.get("name") and category_name_exists(data["name"], excluded_category_id=excluded_category_id):
        raise AdminCategoryError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"name": ["Name is already used by another category."]},
        )


def create_admin_category(data):
    ensure_category_can_use_payload(data)
    category = Category(
        name=data["name"],
        slug=data["slug"],
        description=data.get("description") or None,
        is_active=data.get("is_active", True),
        sort_order=data.get("sort_order", 0),
    )
    db.session.add(category)
    db.session.commit()
    return category


def update_admin_category(category, data):
    ensure_category_can_use_payload(data, category=category)

    for field_name in ("name", "slug", "description", "is_active", "sort_order"):
        if field_name in data:
            value = data[field_name]
            if field_name == "description":
                value = value or None
            setattr(category, field_name, value)

    db.session.commit()
    return category


def update_admin_category_status(category, is_active):
    category.is_active = is_active
    db.session.commit()
    return category


def get_admin_product_by_slug(slug):
    return (
        Product.query.options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.seller),
        )
        .filter(Product.slug == slug)
        .one_or_none()
    )


def product_slug_exists(slug, excluded_product_id=None):
    query = Product.query.filter(Product.slug == slug)
    if excluded_product_id is not None:
        query = query.filter(Product.id != excluded_product_id)
    return db.session.query(query.exists()).scalar()


def ensure_product_can_use_payload(data, product=None):
    category_slug = data.get("category_slug")
    if category_slug and get_category_by_slug(category_slug) is None:
        raise AdminProductError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"category_slug": ["Category was not found."]},
        )

    slug = data.get("slug")
    excluded_product_id = product.id if product is not None else None
    if slug and product_slug_exists(slug, excluded_product_id=excluded_product_id):
        raise AdminProductError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"slug": ["Slug is already used by another product."]},
        )


def set_product_images(product, images):
    if images is None:
        return

    if product.id is not None and product.images:
        for existing_image in list(product.images):
            db.session.delete(existing_image)
        product.images.clear()
        db.session.flush()
    else:
        product.images.clear()

    for index, image_data in enumerate(images):
        product.images.append(
            ProductImage(
                image_url=image_data["image_url"],
                alt_text=image_data["alt_text"],
                sort_order=image_data.get("sort_order", index),
                is_primary=image_data.get("is_primary", False),
            )
        )

    if product.images and not any(image.is_primary for image in product.images):
        product.images[0].is_primary = True


def apply_product_status(product, status):
    if status == ProductStatus.AVAILABLE.value:
        if product.quantity <= 0:
            raise AdminProductError(
                message="Request validation failed.",
                status_code=422,
                code="validation_error",
                details={"quantity": ["Available products must have at least one item in stock."]},
            )
        if product.status != ProductStatus.AVAILABLE.value:
            product.publish()
        return

    if status == ProductStatus.RESERVED.value and product.quantity <= 0:
        raise AdminProductError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"quantity": ["Reserved products must have at least one item in stock."]},
        )

    if status == ProductStatus.SOLD.value:
        product.status = status
        product.quantity = 0
        return

    if status:
        product.status = status


def create_admin_product(seller, data):
    ensure_product_can_use_payload(data)
    category = get_category_by_slug(data["category_slug"])
    product = Product(
        seller=seller,
        category=category,
        title=data["title"],
        slug=data["slug"],
        description=data["description"],
        price_cents=data["price_cents"],
        condition=data["condition"],
        status=ProductStatus.DRAFT.value,
        quantity=data["quantity"],
        brand=data.get("brand") or None,
        color=data.get("color") or None,
        material=data.get("material") or None,
        dimensions=data.get("dimensions") or None,
    )
    set_product_images(product, data.get("images"))
    apply_product_status(product, data.get("status", ProductStatus.DRAFT.value))
    db.session.add(product)
    db.session.commit()
    return product


def update_admin_product(product, data):
    ensure_product_can_use_payload(data, product=product)

    if "category_slug" in data:
        product.category = get_category_by_slug(data["category_slug"])
    for field_name in ("title", "slug", "description", "price_cents", "condition", "quantity", "brand", "color", "material", "dimensions"):
        if field_name in data:
            value = data[field_name]
            if field_name in {"brand", "color", "material", "dimensions"}:
                value = value or None
            setattr(product, field_name, value)

    set_product_images(product, data.get("images"))
    if "status" in data:
        apply_product_status(product, data["status"])
    elif product.status == ProductStatus.AVAILABLE.value and product.quantity <= 0:
        apply_product_status(product, ProductStatus.AVAILABLE.value)

    db.session.commit()
    return product


def update_admin_product_status(product, status):
    apply_product_status(product, status)
    db.session.commit()
    return product


def update_admin_product_quantity(product, quantity):
    if product.status in {ProductStatus.AVAILABLE.value, ProductStatus.RESERVED.value} and quantity <= 0:
        raise AdminProductError(
            message="Request validation failed.",
            status_code=422,
            code="validation_error",
            details={"quantity": ["Active products must have at least one item in stock."]},
        )

    product.quantity = quantity
    db.session.commit()
    return product


def list_admin_products(filters):
    query = admin_products_query()

    search = (filters.get("q") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.title.ilike(pattern),
                Product.description.ilike(pattern),
                Product.slug.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.material.ilike(pattern),
            )
        )

    category = (filters.get("category") or "").strip()
    if category:
        query = query.filter(Category.slug == category)

    status = (filters.get("status") or "").strip()
    if status:
        query = query.filter(Product.status == status)

    condition = (filters.get("condition") or "").strip()
    if condition:
        query = query.filter(Product.condition == condition)

    sort = filters.get("sort") or "recent"
    if sort == "title_asc":
        query = query.order_by(Product.title.asc(), Product.id.asc())
    elif sort == "price_asc":
        query = query.order_by(Product.price_cents.asc(), Product.id.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price_cents.desc(), Product.id.asc())
    elif sort == "quantity_asc":
        query = query.order_by(Product.quantity.asc(), Product.id.asc())
    elif sort == "quantity_desc":
        query = query.order_by(Product.quantity.desc(), Product.id.asc())
    else:
        query = query.order_by(Product.updated_at.desc(), Product.id.desc())

    return query.all()


def parse_admin_product_filters(args):
    filters = {
        "q": args.get("q", ""),
        "category": args.get("category", ""),
        "status": args.get("status", ""),
        "condition": args.get("condition", ""),
        "sort": args.get("sort", "recent"),
    }
    errors = {}

    if filters["sort"] not in ADMIN_PRODUCT_SORTS:
        errors.setdefault("sort", []).append(
            "Sort must be recent, title_asc, price_asc, price_desc, quantity_asc, or quantity_desc."
        )

    if filters["status"] and filters["status"] not in ADMIN_PRODUCT_STATUSES:
        errors.setdefault("status", []).append("Status must be draft, available, reserved, sold, or hidden.")

    if filters["condition"] and filters["condition"] not in ADMIN_PRODUCT_CONDITIONS:
        errors.setdefault("condition", []).append(
            "Condition must be new_other, like_new, good, fair, or for_repair."
        )

    return filters, errors
