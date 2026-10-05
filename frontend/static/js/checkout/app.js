class SecondMarketCheckoutApp {
    constructor() {
        this.state = {
            currentView: "cart",
            user: null,
            cart: null,
            orderConfirmation: null,
            loading: true,
            actionLoading: false,
            error: "",
        };
        this.templateCache = {};
        this.init();
    }

    async init() {
        this.render();
        await this.loadCurrentUser();
        if (this.state.user?.role === "buyer") {
            await this.refreshCart();
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

    async refreshCart() {
        if (!window.SecondMarketCheckoutAPI) {
            this.state.error = "The checkout API client is unavailable.";
            this.state.loading = false;
            this.render();
            return;
        }

        this.state.loading = true;
        this.state.error = "";
        this.render();

        try {
            this.state.cart = await window.SecondMarketCheckoutAPI.getCart();
        } catch (error) {
            this.state.error = window.SecondMarketCheckoutAPI.formatError(error);
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    parsePositiveInteger(value, fieldLabel) {
        const parsed = parseInt(value, 10);
        if (Number.isNaN(parsed) || parsed < 1) {
            throw new Error(`${fieldLabel} must be at least 1.`);
        }
        return parsed;
    }

    async updateCartItemQuantity(event, productSlug) {
        event.preventDefault();
        if (this.state.actionLoading) return;

        const form = new FormData(event.currentTarget);
        let quantity;

        try {
            quantity = this.parsePositiveInteger(form.get("quantity"), "Quantity");
        } catch (error) {
            this.showToast(error.message, "error");
            return;
        }

        try {
            this.state.actionLoading = true;
            this.render();
            this.state.cart = await window.SecondMarketCheckoutAPI.updateItem(productSlug, quantity);
            this.showToast("Cart quantity updated.");
        } catch (error) {
            this.showToast(window.SecondMarketCheckoutAPI.formatError(error), "error");
        } finally {
            this.state.actionLoading = false;
            this.render();
        }
    }

    async removeCartItem(productSlug) {
        if (this.state.actionLoading) return;

        try {
            this.state.actionLoading = true;
            this.render();
            this.state.cart = await window.SecondMarketCheckoutAPI.removeItem(productSlug);
            this.showToast("Item removed from cart.", "info");
        } catch (error) {
            this.showToast(window.SecondMarketCheckoutAPI.formatError(error), "error");
        } finally {
            this.state.actionLoading = false;
            this.render();
        }
    }

    checkoutPayloadFromForm(formElement) {
        const form = new FormData(formElement);
        return {
            shipping_address: {
                recipient_name: (form.get("recipient_name") || "").toString().trim(),
                phone: (form.get("phone") || "").toString().trim(),
                address_line1: (form.get("address_line1") || "").toString().trim(),
                address_line2: (form.get("address_line2") || "").toString().trim(),
                city: (form.get("city") || "").toString().trim(),
                province: (form.get("province") || "").toString().trim(),
                postal_code: (form.get("postal_code") || "").toString().trim(),
                country: "Philippines",
            },
            payment_method: (form.get("payment_method") || "").toString(),
        };
    }

    async submitCheckout(event) {
        event.preventDefault();
        if (this.state.actionLoading) return;

        try {
            this.state.actionLoading = true;
            this.render();
            const payload = this.checkoutPayloadFromForm(event.currentTarget);
            this.state.orderConfirmation = await window.SecondMarketCheckoutAPI.confirmOrder(payload);
            this.state.cart = await window.SecondMarketCheckoutAPI.getCart();
            this.showToast("Order placed successfully.");
        } catch (error) {
            this.showToast(window.SecondMarketCheckoutAPI.formatError(error), "error");
        } finally {
            this.state.actionLoading = false;
            this.render();
        }
    }

    navigate(viewName) {
        if (viewName === "cart") {
            this.state.orderConfirmation = null;
        }
        this.state.currentView = viewName;
        this.render();
        document.getElementById("checkout-main-content")?.focus();
    }

    loadPageTemplate(templateName) {
        if (this.templateCache[templateName]) {
            return this.templateCache[templateName];
        }

        const request = new XMLHttpRequest();
        request.open("GET", `/checkout/pages/${templateName}.html`, false);
        request.send(null);

        if (request.status < 200 || request.status >= 300) {
            return `
                <section class="checkout-state-panel">
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

    renderCartStatus() {
        if (this.state.loading) {
            return `<div class="checkout-state-panel"><h1>Loading Cart</h1><p>Your saved cart is being prepared.</p></div>`;
        }

        if (this.state.error) {
            return `<div class="checkout-state-panel"><h1>Unable To Load Cart</h1><p>${this.escapeHtml(this.state.error)}</p></div>`;
        }

        return "";
    }

    render() {
        const main = document.getElementById("checkout-main-content");
        if (!main) return;

        this.updateUserDisplay();
        this.updateNavigation();

        if (!this.state.user) {
            main.innerHTML = this.renderAccessPanel(
                "Buyer Sign In Required",
                "Sign in with a buyer account to review your cart and continue checkout.",
                "/login.html",
                "Go To Sign In"
            );
            return;
        }

        if (this.state.user.role !== "buyer") {
            main.innerHTML = this.renderAccessPanel(
                "Buyer Access Required",
                "Admin seller accounts cannot place buyer checkout orders.",
                "/",
                "Back To Storefront"
            );
            return;
        }

        if (this.state.currentView === "summary") {
            main.innerHTML = window.SecondMarketCheckoutPages.renderSummaryPage.call(this);
            return;
        }

        main.innerHTML = window.SecondMarketCheckoutPages.renderCartPage.call(this);
    }

    renderAccessPanel(title, message, href, actionText) {
        return `
            <section class="checkout-state-panel" aria-live="polite">
                <h1>${this.escapeHtml(title)}</h1>
                <p>${this.escapeHtml(message)}</p>
                <a href="${href}" class="checkout-primary-button">${this.escapeHtml(actionText)}</a>
            </section>
        `;
    }

    updateUserDisplay() {
        const label = document.querySelector("[data-checkout-user-name]");
        if (!label) return;
        label.textContent = this.state.user
            ? `${this.state.user.first_name} ${this.state.user.last_name}`
            : "Not signed in";
    }

    updateNavigation() {
        document.querySelectorAll("[data-checkout-nav]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.checkoutNav === this.state.currentView);
        });
    }

    actionDisabledAttribute() {
        return this.state.actionLoading ? "disabled" : "";
    }

    showToast(message, type = "success") {
        const container = document.getElementById("checkout-toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `checkout-toast ${type === "error" ? "is-error" : ""}`;
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

let checkoutApp;
window.addEventListener("DOMContentLoaded", () => {
    checkoutApp = new SecondMarketCheckoutApp();
});
