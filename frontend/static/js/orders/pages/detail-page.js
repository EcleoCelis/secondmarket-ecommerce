(function () {
    function renderOrderItem(item) {
        return `
            <article class="orders-line-item">
                <div>
                    <h2>${this.escapeHtml(item.product_title)}</h2>
                    <p>Qty ${this.escapeHtml(item.quantity)} | ${this.formatPrice(item.unit_price)}</p>
                </div>
                <strong>${this.formatPrice(item.line_total)}</strong>
            </article>
        `;
    }

    function renderAddress(order) {
        const shipping = order?.shipping_record;
        if (!shipping) {
            return "<p>No shipping address is attached to this order.</p>";
        }

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

    function renderTrackingPanel(order) {
        const shipping = order?.shipping_record;
        const trackingNumber = shipping?.tracking_number || "Not assigned yet";
        const trackingSteps = [
            { key: "not_ready", label: "Order Confirmed" },
            { key: "ready", label: "Ready For Fulfillment" },
            { key: "shipped", label: "Shipped" },
            { key: "delivered", label: "Delivered" },
        ];
        const currentIndex = Math.max(0, trackingSteps.findIndex((step) => step.key === order.shipping_status));
        const steps = trackingSteps.map((step, index) => `
            <li class="${index <= currentIndex ? "is-active" : ""}">
                <span>${this.escapeHtml(step.label)}</span>
            </li>
        `).join("");

        return `
            <section class="orders-panel orders-tracking-panel" aria-label="Fulfillment tracking">
                <div class="orders-panel-header">
                    <h2>Tracking</h2>
                    ${this.statusBadge(order.shipping_status)}
                </div>
                <div class="orders-tracking-body">
                    <p><strong>Tracking Number</strong><br>${this.escapeHtml(trackingNumber)}</p>
                    <ol class="orders-tracking-steps">
                        ${steps}
                    </ol>
                </div>
            </section>
        `;
    }

    function renderCancellationAction(order) {
        const canCancel = ["pending", "confirmed"].includes(order.status) && order.shipping_status === "not_ready";
        if (!canCancel) {
            return `<p class="orders-cancel-note">Cancellation is available only before fulfillment begins.</p>`;
        }

        return `
            <button type="button" class="orders-danger-button" onclick="ordersApp.cancelOrder('${this.escapeAttribute(order.order_number)}')" ${this.actionDisabledAttribute()}>
                Cancel Order
            </button>
        `;
    }

    function renderDetailPage() {
        const order = this.state.currentOrder;
        if (!order) {
            return this.renderPageTemplate("detail", {
                ordersStatus: this.renderOrdersStatus(),
                orderNumber: "Order Detail",
                itemCount: 0,
                orderItems: "",
                orderTotal: this.formatPrice({ amount: 0 }),
                orderStatus: "Not loaded",
                paymentStatus: "Not loaded",
                shippingStatus: "Not loaded",
                placedAt: "Not loaded",
                shippingAddress: "",
                trackingPanel: "",
                cancellationAction: "",
            });
        }

        return this.renderPageTemplate("detail", {
            ordersStatus: this.renderOrdersStatus(),
            orderNumber: this.escapeHtml(order.order_number),
            itemCount: order.item_count || (order.items || []).length,
            orderItems: (order.items || []).map((item) => renderOrderItem.call(this, item)).join(""),
            orderTotal: this.formatPrice(order.total),
            orderStatus: this.statusBadge(order.status),
            paymentStatus: this.statusBadge(order.payment_status),
            shippingStatus: this.statusBadge(order.shipping_status),
            placedAt: this.escapeHtml(this.formatDate(order.placed_at)),
            shippingAddress: renderAddress.call(this, order),
            trackingPanel: renderTrackingPanel.call(this, order),
            cancellationAction: renderCancellationAction.call(this, order),
        });
    }

    window.SecondMarketOrdersPages = window.SecondMarketOrdersPages || {};
    window.SecondMarketOrdersPages.renderDetailPage = renderDetailPage;
})();
