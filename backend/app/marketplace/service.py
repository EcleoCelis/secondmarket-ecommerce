from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from backend.app.extensions import db
from backend.app.models import Category, Product, ProductCondition, ProductImage, ProductStatus, WishlistItem


ALLOWED_SORTS = {"recent", "price_asc", "price_desc", "title_asc"}
ALLOWED_CONDITIONS = {condition.value for condition in ProductCondition}


def list_active_categories():
    product_counts = dict(
        db.session.query(Product.category_id, func.count(Product.id))
        .filter(Product.status == ProductStatus.AVAILABLE.value, Product.quantity > 0)
        .group_by(Product.category_id)
        .all()
    )

    categories = (
        Category.query.filter_by(is_active=True)
        .order_by(Category.sort_order.asc(), Category.name.asc())
        .all()
    )
    return [(category, product_counts.get(category.id, 0)) for category in categories]


def marketplace_products_query():
    return (
        Product.query.options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.seller),
        )
        .join(Category)
        .filter(
            Product.status == ProductStatus.AVAILABLE.value,
            Product.quantity > 0,
            Category.is_active.is_(True),
        )
    )


def list_marketplace_products(filters):
    query = marketplace_products_query()

    search = (filters.get("q") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.title.ilike(pattern),
                Product.description.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.material.ilike(pattern),
            )
        )

    category = (filters.get("category") or "").strip()
    if category:
        query = query.filter(Category.slug == category)

    condition = (filters.get("condition") or "").strip()
    if condition:
        query = query.filter(Product.condition == condition)

    min_price = filters.get("min_price_cents")
    if min_price is not None:
        query = query.filter(Product.price_cents >= min_price)

    max_price = filters.get("max_price_cents")
    if max_price is not None:
        query = query.filter(Product.price_cents <= max_price)

    sort = filters.get("sort") or "recent"
    if sort == "price_asc":
        query = query.order_by(Product.price_cents.asc(), Product.id.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price_cents.desc(), Product.id.asc())
    elif sort == "title_asc":
        query = query.order_by(Product.title.asc(), Product.id.asc())
    else:
        query = query.order_by(Product.listed_at.desc().nullslast(), Product.id.desc())

    return query.all()


def get_marketplace_product_by_slug(slug):
    return marketplace_products_query().filter(Product.slug == slug).one_or_none()


def list_wishlist_items(user):
    return (
        WishlistItem.query.options(
            selectinload(WishlistItem.product).selectinload(Product.category),
            selectinload(WishlistItem.product).selectinload(Product.images),
        )
        .join(Product)
        .join(Category)
        .filter(
            WishlistItem.user_id == user.id,
            Product.status == ProductStatus.AVAILABLE.value,
            Product.quantity > 0,
            Category.is_active.is_(True),
        )
        .order_by(WishlistItem.created_at.desc(), WishlistItem.id.desc())
        .all()
    )


def get_wishlist_item(user, product):
    return WishlistItem.query.filter_by(user_id=user.id, product_id=product.id).one_or_none()


def add_wishlist_item(user, product):
    wishlist_item = get_wishlist_item(user, product)
    created = False
    if wishlist_item is None:
        wishlist_item = WishlistItem(user=user, product=product)
        db.session.add(wishlist_item)
        db.session.commit()
        created = True
    return wishlist_item, created


def remove_wishlist_item(user, product):
    wishlist_item = get_wishlist_item(user, product)
    if wishlist_item is None:
        return False

    db.session.delete(wishlist_item)
    db.session.commit()
    return True


def parse_price_cents(value, field_name):
    if value in (None, ""):
        return None, None

    try:
        parsed = int(value)
    except ValueError:
        return None, f"{field_name} must be an integer number of cents."

    if parsed < 0:
        return None, f"{field_name} cannot be negative."

    return parsed, None


def parse_marketplace_filters(args):
    filters = {
        "q": args.get("q", ""),
        "category": args.get("category", ""),
        "condition": args.get("condition", ""),
        "sort": args.get("sort", "recent"),
    }
    errors = {}

    if filters["sort"] not in ALLOWED_SORTS:
        errors.setdefault("sort", []).append("Sort must be recent, price_asc, price_desc, or title_asc.")

    if filters["condition"] and filters["condition"] not in ALLOWED_CONDITIONS:
        errors.setdefault("condition", []).append(
            "Condition must be new_other, like_new, good, fair, or for_repair."
        )

    min_price, min_error = parse_price_cents(args.get("min_price_cents"), "min_price_cents")
    max_price, max_error = parse_price_cents(args.get("max_price_cents"), "max_price_cents")
    if min_error:
        errors.setdefault("min_price_cents", []).append(min_error)
    if max_error:
        errors.setdefault("max_price_cents", []).append(max_error)
    if min_price is not None and max_price is not None and min_price > max_price:
        errors.setdefault("price", []).append("min_price_cents cannot be greater than max_price_cents.")

    filters["min_price_cents"] = min_price
    filters["max_price_cents"] = max_price
    return filters, errors
