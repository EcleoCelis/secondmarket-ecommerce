from backend.app.marketplace.serializers import format_price, serialize_category


def primary_image_for(product):
    primary_image = next((image for image in product.images if image.is_primary), None)
    return primary_image or (product.images[0] if product.images else None)


def serialize_admin_category(category, product_count=0):
    data = serialize_category(category)
    data["product_count"] = product_count
    return data


def serialize_admin_product(product):
    primary_image = primary_image_for(product)

    return {
        "id": product.id,
        "title": product.title,
        "slug": product.slug,
        "description": product.description,
        "price": format_price(product.price_cents),
        "condition": product.condition,
        "status": product.status,
        "quantity": product.quantity,
        "brand": product.brand,
        "color": product.color,
        "material": product.material,
        "dimensions": product.dimensions,
        "listed_at": product.listed_at.isoformat() if product.listed_at else None,
        "category": serialize_category(product.category),
        "seller": {
            "id": product.seller.id,
            "name": f"{product.seller.first_name} {product.seller.last_name}".strip(),
            "email": product.seller.email,
        },
        "primary_image": {
            "id": primary_image.id,
            "url": primary_image.image_url,
            "alt_text": primary_image.alt_text,
        } if primary_image else None,
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
