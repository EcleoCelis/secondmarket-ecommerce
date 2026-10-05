(function () {
    function optionList(options, selectedValue) {
        return options.map((option) => `
            <option value="${option.value}" ${option.value === selectedValue ? "selected" : ""}>${option.label}</option>
        `).join("");
    }

    function renderOrderCard(order) {
        return `
            <article class="orders-card">
                <div>
                    <p class="orders-eyebrow">${this.escapeHtml(order.order_number)}</p>
                    <h2>${this.formatPrice(order.total)}</h2>
                    <p>${this.escapeHtml(order.item_count)} item(s) | Placed ${this.escapeHtml(this.formatDate(order.placed_at))}</p>
                </div>
                <div class="orders-card-status">
                    ${this.statusBadge(order.status)}
                    ${this.statusBadge(order.shipping_status)}
                    <button type="button" class="orders-secondary-button" onclick="ordersApp.loadOrder('${this.escapeAttribute(order.order_number)}')">View Details</button>
                </div>
            </article>
        `;
    }

    function renderHistoryPage() {
        const orders = this.state.orders || [];
        const orderCards = orders.map((order) => renderOrderCard.call(this, order)).join("") || `
            <div class="orders-empty-state">
                <h2>No orders yet</h2>
                <p>Your confirmed SecondMarket purchases will appear here.</p>
                <a href="/" class="orders-primary-button">Browse Marketplace</a>
            </div>
        `;

        return this.renderPageTemplate("history", {
            ordersStatus: this.renderOrdersStatus(),
            orderCards,
            statusOptions: optionList([
                { value: "all", label: "All Statuses" },
                { value: "confirmed", label: "Confirmed" },
                { value: "processing", label: "Processing" },
                { value: "shipped", label: "Shipped" },
                { value: "delivered", label: "Delivered" },
                { value: "cancelled", label: "Cancelled" },
            ], this.state.filters.status),
            paymentOptions: optionList([
                { value: "all", label: "All Payments" },
                { value: "pending", label: "Pending" },
                { value: "paid", label: "Paid" },
                { value: "failed", label: "Failed" },
                { value: "refunded", label: "Refunded" },
            ], this.state.filters.payment_status),
            shippingOptions: optionList([
                { value: "all", label: "All Shipping" },
                { value: "not_ready", label: "Not Ready" },
                { value: "ready", label: "Ready" },
                { value: "shipped", label: "Shipped" },
                { value: "delivered", label: "Delivered" },
                { value: "returned", label: "Returned" },
            ], this.state.filters.shipping_status),
            sortOptions: optionList([
                { value: "recent", label: "Recently Placed" },
                { value: "oldest", label: "Oldest First" },
                { value: "total_desc", label: "Total High To Low" },
                { value: "total_asc", label: "Total Low To High" },
            ], this.state.filters.sort),
        });
    }

    window.SecondMarketOrdersPages = window.SecondMarketOrdersPages || {};
    window.SecondMarketOrdersPages.renderHistoryPage = renderHistoryPage;
})();
