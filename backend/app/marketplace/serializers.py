def format_price(price_cents):
    return {
        "amount_cents": price_cents,
        "amount": round(price_cents / 100, 2),
        "currency": "PHP",
    }


def serialize_category(category, product_count=None):
    data = {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "is_active": category.is_active,
        "sort_order": category.sort_order,
    }

    if product_count is not None:
        data["product_count"] = product_count

    return data


def serialize_product_summary(product):
    primary_image = next((image for image in product.images if image.is_primary), None)
    if primary_image is None and product.images:
        primary_image = product.images[0]

    return {
        "id": product.id,
        "title": product.title,
        "slug": product.slug,
        "description": product.description,
        "price": format_price(product.price_cents),
        "condition": product.condition,
        "status": product.status,
        "quantity": product.quantity,
        "category": serialize_category(product.category),
        "primary_image": {
            "url": primary_image.image_url,
            "alt_text": primary_image.alt_text,
        } if primary_image else None,
        "listed_at": product.listed_at.isoformat() if product.listed_at else None,
    }


def serialize_product_detail(product):
    data = serialize_product_summary(product)
    data.update(
        {
            "brand": product.brand,
            "color": product.color,
            "material": product.material,
            "dimensions": product.dimensions,
            "seller": {
                "id": product.seller.id,
                "name": f"{product.seller.first_name} {product.seller.last_name}".strip(),
            },
            "images": [
                {
                    "id": image.id,
                    "url": image.image_url,
                    "alt_text": image.alt_text,
                    "sort_order": image.sort_order,
                    "is_primary": image.is_primary,
                }
                for image in product.images
            ],
        }
    )
    return data
