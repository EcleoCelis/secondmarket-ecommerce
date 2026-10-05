(function () {
    function renderConfirmationPanel() {
        const confirmation = this.state.orderConfirmation;
        if (!confirmation) return "";

        return `
            <div class="checkout-confirmation-panel" aria-live="polite">
                <span>Order Confirmed</span>
                <strong>${this.escapeHtml(confirmation.order.order_number)}</strong>
                <p>Total: ${this.formatPrice(confirmation.order.total)}</p>
                <a href="/orders?order=${this.escapeAttribute(confirmation.order.order_number)}" class="checkout-secondary-link">View Order</a>
            </div>
        `;
    }

    function renderSummaryPage() {
        const cart = this.state.cart || { items: [], total_items: 0, subtotal: { amount: 0 } };
        const hasItems = (cart.items || []).length > 0;

        return this.renderPageTemplate("summary", {
            cartStatus: this.renderCartStatus(),
            cartTotalItems: cart.total_items || 0,
            cartSubtotal: this.formatPrice(cart.subtotal),
            checkoutDisabled: hasItems && !this.state.actionLoading ? "" : "disabled",
            confirmationPanel: renderConfirmationPanel.call(this),
        });
    }

    window.SecondMarketCheckoutPages = window.SecondMarketCheckoutPages || {};
    window.SecondMarketCheckoutPages.renderSummaryPage = renderSummaryPage;
})();
