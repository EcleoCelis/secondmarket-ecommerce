from uuid import uuid4

from backend.app.cart.service import get_or_create_active_cart
from backend.app.extensions import db
from backend.app.models import (
    CartStatus,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    ProductStatus,
    ShippingRecord,
    ShippingStatus,
)


FREE_SHIPPING_THRESHOLD_CENTS = 300000
STANDARD_SHIPPING_CENTS = 4500


class CheckoutError(Exception):
    def __init__(self, message, status_code=400, code="checkout_error", details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


def shipping_cents_for_subtotal(subtotal_cents):
    if subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS:
        return 0
    return STANDARD_SHIPPING_CENTS


def validate_cart_for_checkout(cart):
    if not cart.items:
        raise CheckoutError(
            message="Your cart is empty.",
            status_code=409,
            code="cart_empty",
        )

    errors = {}
    for item in cart.items:
        product = item.product
        field_name = product.slug
        if not product.is_available:
            errors.setdefault(field_name, []).append("Product is no longer available.")
        elif item.quantity > product.quantity:
            errors.setdefault(field_name, []).append(f"Only {product.quantity} item(s) are available.")

    if errors:
        raise CheckoutError(
            message="Some cart items are no longer available for checkout.",
            status_code=409,
            code="cart_not_checkout_ready",
            details={"items": errors},
        )


def build_checkout_draft(user, checkout_data):
    cart = get_or_create_active_cart(user)
    validate_cart_for_checkout(cart)

    subtotal_cents = cart.subtotal_cents
    shipping_cents = shipping_cents_for_subtotal(subtotal_cents)
    total_cents = subtotal_cents + shipping_cents

    return {
        "cart": cart,
        "shipping_address": checkout_data["shipping_address"],
        "payment_method": checkout_data["payment_method"],
        "subtotal_cents": subtotal_cents,
        "shipping_cents": shipping_cents,
        "total_cents": total_cents,
    }


def generate_order_number():
    return f"SM-{uuid4().hex[:10].upper()}"


def place_checkout_order(user, checkout_data):
    draft = build_checkout_draft(user, checkout_data)
    cart = draft["cart"]
    shipping_address = draft["shipping_address"]

    order = Order(
        user=user,
        order_number=generate_order_number(),
        status=OrderStatus.CONFIRMED.value,
        payment_status=PaymentStatus.PENDING.value,
        shipping_status=ShippingStatus.NOT_READY.value,
        subtotal_cents=draft["subtotal_cents"],
        shipping_cents=draft["shipping_cents"],
        total_cents=draft["total_cents"],
    )
    order.mark_placed()

    for cart_item in cart.items:
        product = cart_item.product
        product.quantity -= cart_item.quantity
        if product.quantity == 0:
            product.status = ProductStatus.SOLD.value

        order.items.append(
            OrderItem(
                product=product,
                product_title=product.title,
                quantity=cart_item.quantity,
                unit_price_cents=cart_item.unit_price_cents,
            )
        )

    order.payments.append(
        Payment(
            method=checkout_data["payment_method"],
            status=PaymentStatus.PENDING.value,
            amount_cents=draft["total_cents"],
            reference_number=f"PAY-{uuid4().hex[:12].upper()}",
        )
    )
    order.shipping_record = ShippingRecord(
        recipient_name=shipping_address["recipient_name"],
        phone=shipping_address["phone"],
        address_line1=shipping_address["address_line1"],
        address_line2=shipping_address.get("address_line2"),
        city=shipping_address["city"],
        province=shipping_address["province"],
        postal_code=shipping_address["postal_code"],
        country=shipping_address.get("country") or "Philippines",
        status=ShippingStatus.NOT_READY.value,
    )
    cart.status = CartStatus.CHECKED_OUT.value

    db.session.add(order)
    db.session.commit()
    return order
