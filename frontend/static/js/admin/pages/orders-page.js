(function () {
    function optionList(options, selectedValue) {
        return options.map((option) => `
            <option value="${option.value}" ${option.value === selectedValue ? "selected" : ""}>${option.label}</option>
        `).join("");
    }

    function renderOrderRows() {
        const orders = this.state.orders || [];
        const disabled = this.actionDisabledAttribute();

        return orders.map((order) => `
            <tr>
                <td>
                    <strong>${this.escapeHtml(order.order_number)}</strong>
                    <div class="admin-muted">${this.escapeHtml(this.formatDate(order.placed_at))}</div>
                </td>
                <td>
                    <strong>${this.escapeHtml(order.buyer?.name || "Buyer")}</strong>
                    <div class="admin-muted">${this.escapeHtml(order.buyer?.email || "No email")}</div>
                </td>
                <td>${this.formatPrice(order.total)}</td>
                <td>${this.statusBadge(order.status)}</td>
                <td>${this.statusBadge(order.payment_status)}</td>
                <td>${this.statusBadge(order.shipping_status)}</td>
                <td>
                    <button data-admin-action type="button" class="admin-button-secondary" onclick="adminApp.loadAdminOrder('${this.escapeAttribute(order.order_number)}')" ${disabled}>View</button>
                </td>
            </tr>
        `).join("") || this.emptyTableRow("No orders match the selected filters.", 7);
    }

    function renderOrderItems(order) {
        return (order.items || []).map((item) => `
            <article class="admin-order-line-item">
                <div>
                    <strong>${this.escapeHtml(item.product_title)}</strong>
                    <span>Qty ${this.escapeHtml(item.quantity)} at ${this.formatPrice(item.unit_price)}</span>
                </div>
                <strong>${this.formatPrice(item.line_total)}</strong>
            </article>
        `).join("");
    }

    function renderShippingAddress(order) {
        const shipping = order.shipping_record;
        if (!shipping) return "<p>No shipping address is attached to this order.</p>";

        return `
            <p>
                <strong>${this.escapeHtml(shipping.recipient_name)}</strong><br>
                ${this.escapeHtml(shipping.phone)}<br>
                ${this.escapeHtml(shipping.address_line1)}${shipping.address_line2 ? `, ${this.escapeHtml(shipping.address_line2)}` : ""}<br>
                ${this.escapeHtml(shipping.city)}, ${this.escapeHtml(shipping.province)} ${this.escapeHtml(shipping.postal_code)}<br>
                ${this.escapeHtml(shipping.country)}
            </p>
        `;
    }

    function renderOrderDetail() {
        const order = this.state.currentOrder;
        if (!order) {
            return `
                <aside id="admin-order-detail" class="admin-panel admin-order-detail" tabindex="-1">
                    <div class="admin-panel-header">
                        <h3>Order Detail</h3>
                    </div>
                    <div class="admin-detail-empty">
                        <p>Select an order to review buyer details, item snapshots, payment state, and shipping information.</p>
                    </div>
                </aside>
            `;
        }

        return `
            <aside id="admin-order-detail" class="admin-panel admin-order-detail" tabindex="-1">
                <div class="admin-panel-header">
                    <div>
                        <p class="admin-eyebrow">Selected Order</p>
                        <h3>${this.escapeHtml(order.order_number)}</h3>
                    </div>
                    <span>${this.formatPrice(order.total)}</span>
                </div>
                <div class="admin-order-detail-grid">
                    <section>
                        <h4>Buyer</h4>
                        <p>
                            <strong>${this.escapeHtml(order.buyer?.name || "Buyer")}</strong><br>
                            ${this.escapeHtml(order.buyer?.email || "No email")}
                        </p>
                    </section>
                    <section>
                        <h4>Status</h4>
                        <div class="admin-status-stack">
                            ${this.statusBadge(order.status, "Order: " + order.status)}
                            ${this.statusBadge(order.payment_status, "Payment: " + order.payment_status)}
                            ${this.statusBadge(order.shipping_status, "Shipping: " + order.shipping_status)}
                        </div>
                    </section>
                    <section>
                        <h4>Shipping Address</h4>
                        ${renderShippingAddress.call(this, order)}
                    </section>
                    <section>
                        <h4>Payment</h4>
                        ${(order.payments || []).map((payment) => `
                            <p>${this.escapeHtml(payment.method)}<br>${this.statusBadge(payment.status)} ${this.formatPrice(payment.amount)}</p>
                        `).join("") || "<p>No payment record is attached.</p>"}
                    </section>
                </div>
                <div class="admin-order-items">
                    <h4>Items</h4>
                    ${renderOrderItems.call(this, order)}
                </div>
            </aside>
        `;
    }

    function renderOrdersPage() {
        return this.renderPageTemplate("orders", {
            orderCount: (this.state.orders || []).length,
            orderStatus: this.renderInventoryStatus("Order records are loading."),
            orderRows: renderOrderRows.call(this),
            orderDetail: renderOrderDetail.call(this),
            statusOptions: optionList([
                { value: "all", label: "All Statuses" },
                { value: "confirmed", label: "Confirmed" },
                { value: "processing", label: "Processing" },
                { value: "shipped", label: "Shipped" },
                { value: "delivered", label: "Delivered" },
                { value: "cancelled", label: "Cancelled" },
            ], this.state.orderFilters.status),
            paymentOptions: optionList([
                { value: "all", label: "All Payments" },
                { value: "pending", label: "Pending" },
                { value: "paid", label: "Paid" },
                { value: "failed", label: "Failed" },
                { value: "refunded", label: "Refunded" },
            ], this.state.orderFilters.payment_status),
            shippingOptions: optionList([
                { value: "all", label: "All Shipping" },
                { value: "not_ready", label: "Not Ready" },
                { value: "ready", label: "Ready" },
                { value: "shipped", label: "Shipped" },
                { value: "delivered", label: "Delivered" },
                { value: "returned", label: "Returned" },
            ], this.state.orderFilters.shipping_status),
            sortOptions: optionList([
                { value: "recent", label: "Recently Placed" },
                { value: "oldest", label: "Oldest First" },
                { value: "total_desc", label: "Total High To Low" },
                { value: "total_asc", label: "Total Low To High" },
            ], this.state.orderFilters.sort),
        });
    }

    window.SecondMarketAdminPages = window.SecondMarketAdminPages || {};
    window.SecondMarketAdminPages.renderOrdersPage = renderOrdersPage;
})();
