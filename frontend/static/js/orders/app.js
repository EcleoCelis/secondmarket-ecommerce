class SecondMarketOrdersApp {
    constructor() {
        this.state = {
            currentView: "history",
            user: null,
            orders: [],
            currentOrder: null,
            loading: true,
            actionLoading: false,
            error: "",
            filters: {
                status: "all",
                payment_status: "all",
                shipping_status: "all",
                sort: "recent",
            },
        };
        this.templateCache = {};
        this.init();
    }

    async init() {
        this.render();
        await this.loadCurrentUser();
        if (this.state.user?.role === "buyer") {
            const orderNumber = this.initialOrderNumber();
            if (orderNumber) {
                await this.loadOrder(orderNumber);
                return;
            }

            await this.refreshOrders();
        }
    }

    async loadCurrentUser() {
        try {
            const payload = await window.SecondMarketAuthAPI.me();
            this.state.user = payload.data.authenticated ? payload.data.user : null;
        } catch (error) {
            this.state.user = null;
        }
        this.render();
    }

    async refreshOrders() {
        if (!window.SecondMarketOrdersAPI) {
            this.state.error = "The order API client is unavailable.";
            this.state.loading = false;
            this.render();
            return;
        }

        this.state.loading = true;
        this.state.error = "";
        this.render();

        try {
            const result = await window.SecondMarketOrdersAPI.listOrders(this.state.filters);
            this.state.orders = result.orders;
        } catch (error) {
            this.state.error = window.SecondMarketOrdersAPI.formatError(error);
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    async loadOrder(orderNumber) {
        if (!window.SecondMarketOrdersAPI) return;

        this.state.loading = true;
        this.state.error = "";
        this.render();

        try {
            this.state.currentOrder = await window.SecondMarketOrdersAPI.getOrder(orderNumber);
            this.state.currentView = "detail";
            this.syncBrowserUrl("detail", orderNumber);
        } catch (error) {
            this.state.error = window.SecondMarketOrdersAPI.formatError(error);
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    async cancelOrder(orderNumber) {
        if (!window.SecondMarketOrdersAPI || this.state.actionLoading) return;
        if (!window.confirm("Cancel this order before fulfillment begins?")) return;

        try {
            this.state.actionLoading = true;
            this.render();
            this.state.currentOrder = await window.SecondMarketOrdersAPI.cancelOrder(orderNumber);
            await this.refreshOrders();
            this.state.currentView = "detail";
            this.syncBrowserUrl("detail", orderNumber);
            this.showToast("Order cancelled.");
        } catch (error) {
            this.showToast(window.SecondMarketOrdersAPI.formatError(error), "error");
        } finally {
            this.state.actionLoading = false;
            this.render();
        }
    }

    applyFilters(event) {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        this.state.filters = {
            status: (form.get("status") || "all").toString(),
            payment_status: (form.get("payment_status") || "all").toString(),
            shipping_status: (form.get("shipping_status") || "all").toString(),
            sort: (form.get("sort") || "recent").toString(),
        };
        this.refreshOrders();
    }

    navigate(viewName) {
        this.state.currentView = viewName;
        if (viewName === "history") {
            this.state.currentOrder = null;
            this.syncBrowserUrl("history");
        }
        this.render();
        document.getElementById("orders-main-content")?.focus();
    }

    initialOrderNumber() {
        return new URLSearchParams(window.location.search).get("order");
    }

    syncBrowserUrl(viewName, orderNumber = "") {
        if (!window.history?.replaceState) return;

        const nextPath = viewName === "detail" && orderNumber
            ? `/orders?order=${encodeURIComponent(orderNumber)}`
            : "/orders";

        window.history.replaceState({}, "", nextPath);
    }

    loadPageTemplate(templateName) {
        if (this.templateCache[templateName]) {
            return this.templateCache[templateName];
        }

        const request = new XMLHttpRequest();
        request.open("GET", `/orders/pages/${templateName}.html`, false);
        request.send(null);

        if (request.status < 200 || request.status >= 300) {
            return `
                <section class="orders-state-panel">
                    <h1>Page Template Missing</h1>
                    <p>${this.escapeHtml(templateName)} could not be loaded.</p>
                </section>
            `;
        }

        this.templateCache[templateName] = request.responseText;
        return this.templateCache[templateName];
    }

    renderPageTemplate(templateName, replacements = {}) {
        return Object.entries(replacements).reduce(
            (html, [key, value]) => html.replaceAll(`{{${key}}}`, value ?? ""),
            this.loadPageTemplate(templateName)
        );
    }

    renderOrdersStatus() {
        if (this.state.loading) {
            return `<div class="orders-state-panel"><h1>Loading Orders</h1><p>Your order records are being prepared.</p></div>`;
        }

        if (this.state.error) {
            return `<div class="orders-state-panel"><h1>Unable To Load Orders</h1><p>${this.escapeHtml(this.state.error)}</p></div>`;
        }

        return "";
    }

    render() {
        const main = document.getElementById("orders-main-content");
        if (!main) return;

        this.updateUserDisplay();
        this.updateNavigation();

        if (!this.state.user) {
            main.innerHTML = this.renderAccessPanel(
                "Buyer Sign In Required",
                "Sign in with a buyer account to view your SecondMarket orders.",
                "/login.html",
                "Go To Sign In"
            );
            return;
        }

        if (this.state.user.role !== "buyer") {
            main.innerHTML = this.renderAccessPanel(
                "Buyer Access Required",
                "Admin seller accounts should manage orders from the admin workspace.",
                "/admin",
                "Go To Admin"
            );
            return;
        }

        if (this.state.currentView === "detail") {
            main.innerHTML = window.SecondMarketOrdersPages.renderDetailPage.call(this);
            return;
        }

        main.innerHTML = window.SecondMarketOrdersPages.renderHistoryPage.call(this);
    }

    renderAccessPanel(title, message, href, actionText) {
        return `
            <section class="orders-state-panel" aria-live="polite">
                <h1>${this.escapeHtml(title)}</h1>
                <p>${this.escapeHtml(message)}</p>
                <a href="${href}" class="orders-primary-button">${this.escapeHtml(actionText)}</a>
            </section>
        `;
    }

    updateUserDisplay() {
        const label = document.querySelector("[data-orders-user-name]");
        if (!label) return;
        label.textContent = this.state.user
            ? `${this.state.user.first_name} ${this.state.user.last_name}`
            : "Not signed in";
    }

    updateNavigation() {
        document.querySelectorAll("[data-orders-nav]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.ordersNav === this.state.currentView);
        });
    }

    statusBadge(status) {
        return `<span class="orders-badge ${this.escapeAttribute(status)}">${this.escapeHtml(status)}</span>`;
    }

    actionDisabledAttribute() {
        return this.state.actionLoading ? "disabled" : "";
    }

    showToast(message, type = "success") {
        const container = document.getElementById("orders-toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `orders-toast ${type === "error" ? "is-error" : ""}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    formatPrice(price) {
        return `PHP ${(price?.amount || 0).toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        })}`;
    }

    formatDate(value) {
        if (!value) return "Not available";
        return new Date(value).toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }

    escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    escapeAttribute(value) {
        return this.escapeHtml(value).replaceAll("`", "&#096;");
    }
}

let ordersApp;
window.addEventListener("DOMContentLoaded", () => {
    ordersApp = new SecondMarketOrdersApp();
});
