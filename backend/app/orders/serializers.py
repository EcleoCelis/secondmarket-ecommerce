from backend.app.marketplace.serializers import format_price


def serialize_order_item(item):
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_title": item.product_title,
        "quantity": item.quantity,
        "unit_price": format_price(item.unit_price_cents),
        "line_total": format_price(item.line_total_cents),
    }


def serialize_payment(payment):
    if payment is None:
        return None

    return {
        "id": payment.id,
        "method": payment.method,
        "status": payment.status,
        "amount": format_price(payment.amount_cents),
        "reference_number": payment.reference_number,
    }


def serialize_shipping_record(shipping_record):
    if shipping_record is None:
        return None

    return {
        "id": shipping_record.id,
        "recipient_name": shipping_record.recipient_name,
        "phone": shipping_record.phone,
        "address_line1": shipping_record.address_line1,
        "address_line2": shipping_record.address_line2,
        "city": shipping_record.city,
        "province": shipping_record.province,
        "postal_code": shipping_record.postal_code,
        "country": shipping_record.country,
        "tracking_number": shipping_record.tracking_number,
        "status": shipping_record.status,
    }


def serialize_order_summary(order, include_buyer=False):
    data = {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "shipping_status": order.shipping_status,
        "item_count": sum(item.quantity for item in order.items),
        "subtotal": format_price(order.subtotal_cents),
        "shipping": format_price(order.shipping_cents),
        "total": format_price(order.total_cents),
        "placed_at": order.placed_at.isoformat() if order.placed_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }

    if include_buyer:
        data["buyer"] = {
            "id": order.user.id,
            "name": f"{order.user.first_name} {order.user.last_name}".strip(),
            "email": order.user.email,
        }

    return data


def serialize_order_detail(order, include_buyer=False):
    data = serialize_order_summary(order, include_buyer=include_buyer)
    data.update(
        {
            "items": [serialize_order_item(item) for item in order.items],
            "payments": [serialize_payment(payment) for payment in order.payments],
            "shipping_record": serialize_shipping_record(order.shipping_record),
        }
    )
    return data
