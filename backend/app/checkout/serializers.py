from backend.app.cart.serializers import serialize_cart
from backend.app.marketplace.serializers import format_price


def serialize_checkout_draft(draft):
    return {
        "cart": serialize_cart(draft["cart"]),
        "shipping_address": draft["shipping_address"],
        "payment_method": draft["payment_method"],
        "items": [
            {
                "product_id": item.product_id,
                "product_slug": item.product.slug,
                "product_title": item.product.title,
                "quantity": item.quantity,
                "unit_price": format_price(item.unit_price_cents),
                "line_total": format_price(item.line_total_cents),
            }
            for item in draft["cart"].items
        ],
        "totals": {
            "subtotal": format_price(draft["subtotal_cents"]),
            "shipping": format_price(draft["shipping_cents"]),
            "total": format_price(draft["total_cents"]),
        },
    }


def serialize_order_confirmation(order):
    return {
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
            "subtotal": format_price(order.subtotal_cents),
            "shipping": format_price(order.shipping_cents),
            "total": format_price(order.total_cents),
            "placed_at": order.placed_at.isoformat() if order.placed_at else None,
        },
        "items": [
            {
                "product_id": item.product_id,
                "product_title": item.product_title,
                "quantity": item.quantity,
                "unit_price": format_price(item.unit_price_cents),
                "line_total": format_price(item.line_total_cents),
            }
            for item in order.items
        ],
        "payment": {
            "method": order.payments[0].method if order.payments else None,
            "status": order.payments[0].status if order.payments else None,
            "amount": format_price(order.payments[0].amount_cents) if order.payments else format_price(0),
            "reference_number": order.payments[0].reference_number if order.payments else None,
        },
        "shipping_address": {
            "recipient_name": order.shipping_record.recipient_name,
            "phone": order.shipping_record.phone,
            "address_line1": order.shipping_record.address_line1,
            "address_line2": order.shipping_record.address_line2,
            "city": order.shipping_record.city,
            "province": order.shipping_record.province,
            "postal_code": order.shipping_record.postal_code,
            "country": order.shipping_record.country,
            "status": order.shipping_record.status,
        } if order.shipping_record else None,
    }
