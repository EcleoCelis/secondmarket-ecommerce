(function () {
    function renderCartItem(item) {
        const imageUrl = item.product.primary_image?.url || "/static/productImages/bags/young-girl-with-gray-student-backpack.jpg";
        const imageAlt = item.product.primary_image?.alt_text || item.product.title;
        const disabled = this.actionDisabledAttribute();

        return `
            <article class="checkout-cart-item">
                <img src="${this.escapeAttribute(imageUrl)}" alt="${this.escapeAttribute(imageAlt)}" class="checkout-cart-thumb">
                <div>
                    <h2>${this.escapeHtml(item.product.title)}</h2>
                    <p>${this.escapeHtml(item.product.category?.name || "Secondhand item")}</p>
                    <span>${this.escapeHtml(item.product.condition)}</span>
                </div>
                <div class="checkout-cart-meta">
                    <strong>${this.formatPrice(item.line_total)}</strong>
                    <form class="checkout-quantity-form" onsubmit="checkoutApp.updateCartItemQuantity(event, '${this.escapeAttribute(item.product.slug)}')">
                        <label>
                            <span>Qty</span>
                            <input data-checkout-action name="quantity" type="number" min="1" max="${item.max_quantity}" step="1" value="${item.quantity}" ${disabled}>
                        </label>
                        <button data-checkout-action type="submit" ${disabled}>Update</button>
                    </form>
                    <button data-checkout-action type="button" class="checkout-remove-button" onclick="checkoutApp.removeCartItem('${this.escapeAttribute(item.product.slug)}')" ${disabled}>Remove</button>
                </div>
            </article>
        `;
    }

    function renderCartPage() {
        const cart = this.state.cart || { items: [], total_items: 0, subtotal: { amount: 0 } };
        const items = cart.items || [];
        const cartItems = items.map((item) => renderCartItem.call(this, item)).join("") || `
            <div class="checkout-empty-state">
                <h2>Your cart is empty</h2>
                <p>Add a secondhand item from the marketplace before checking out.</p>
                <a href="/" class="checkout-primary-button">Browse Marketplace</a>
            </div>
        `;

        return this.renderPageTemplate("cart", {
            cartStatus: this.renderCartStatus(),
            cartItems,
            cartItemCount: items.length,
            cartTotalItems: cart.total_items || 0,
            cartSubtotal: this.formatPrice(cart.subtotal),
            checkoutDisabled: items.length ? "" : "disabled",
        });
    }

    window.SecondMarketCheckoutPages = window.SecondMarketCheckoutPages || {};
    window.SecondMarketCheckoutPages.renderCartPage = renderCartPage;
})();
