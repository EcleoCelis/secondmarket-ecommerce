class SecondMarketAdminApp {
    constructor() {
        this.state = {
            currentView: "dashboard",
            user: null,
            categories: [],
            products: [],
            orders: [],
            currentOrder: null,
            loading: true,
            actionLoading: false,
            error: "",
            productFilters: {
                q: "",
                status: "all",
                condition: "all",
                sort: "recent",
            },
            orderFilters: {
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
        if (this.state.user?.role === "admin") {
            await this.refreshInventory();
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

    async refreshInventory() {
        if (!window.SecondMarketAdminAPI) {
            this.state.error = "The admin API client is unavailable.";
            this.state.loading = false;
            this.render();
            return;
        }

        this.state.loading = true;
        this.state.error = "";
        this.render();

        try {
            const [categories, productResult] = await Promise.all([
                window.SecondMarketAdminAPI.listCategories(),
                window.SecondMarketAdminAPI.listProducts(this.productQueryParams()),
            ]);
            this.state.categories = categories;
            this.state.products = productResult.products;
            if (window.SecondMarketAdminAPI.listOrders) {
                const orderResult = await window.SecondMarketAdminAPI.listOrders(this.orderQueryParams());
                this.state.orders = orderResult.orders;
            }
        } catch (error) {
            this.state.error = window.SecondMarketAdminAPI.formatError(error);
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    setActionLoading(isLoading) {
        this.state.actionLoading = isLoading;
        this.render();
    }

    actionDisabledAttribute() {
        return this.state.actionLoading ? "disabled" : "";
    }

    parseNonNegativeInteger(value, fieldLabel) {
        const parsed = parseInt(value, 10);
        if (Number.isNaN(parsed) || parsed < 0) {
            throw new Error(`${fieldLabel} must be a non-negative whole number.`);
        }
        return parsed;
    }

    productQueryParams() {
        return {
            q: this.state.productFilters.q,
            status: this.state.productFilters.status,
            condition: this.state.productFilters.condition,
            sort: this.state.productFilters.sort,
        };
    }

    orderQueryParams() {
        return {
            status: this.state.orderFilters.status,
            payment_status: this.state.orderFilters.payment_status,
            shipping_status: this.state.orderFilters.shipping_status,
            sort: this.state.orderFilters.sort,
        };
    }

    applyProductFilters(event) {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        this.state.productFilters = {
            q: (form.get("q") || "").toString().trim(),
            status: (form.get("status") || "all").toString(),
            condition: (form.get("condition") || "all").toString(),
            sort: (form.get("sort") || "recent").toString(),
        };
        this.refreshInventory();
    }

    resetProductFilters() {
        this.state.productFilters = { q: "", status: "all", condition: "all", sort: "recent" };
        this.refreshInventory();
    }

    applyOrderFilters(event) {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        this.state.orderFilters = {
            status: (form.get("status") || "all").toString(),
            payment_status: (form.get("payment_status") || "all").toString(),
            shipping_status: (form.get("shipping_status") || "all").toString(),
            sort: (form.get("sort") || "recent").toString(),
        };
        this.state.currentOrder = null;
        this.refreshInventory();
    }

    resetOrderFilters() {
        this.state.orderFilters = {
            status: "all",
            payment_status: "all",
            shipping_status: "all",
            sort: "recent",
        };
        this.state.currentOrder = null;
        this.refreshInventory();
    }

    async loadAdminOrder(orderNumber) {
        if (!window.SecondMarketAdminAPI?.getOrder) return;

        try {
            this.setActionLoading(true);
            this.state.currentOrder = await window.SecondMarketAdminAPI.getOrder(orderNumber);
            this.render();
            document.getElementById("admin-order-detail")?.focus();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    async setProductStatus(productSlug, status) {
        if (this.state.actionLoading) return;

        try {
            this.setActionLoading(true);
            await window.SecondMarketAdminAPI.updateProductStatus(productSlug, status);
            this.showToast("Product status updated.");
            await this.refreshInventory();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    async setProductQuantity(event, productSlug) {
        event.preventDefault();
        if (this.state.actionLoading) return;

        const form = new FormData(event.currentTarget);
        let quantity;

        try {
            quantity = this.parseNonNegativeInteger(form.get("quantity"), "Quantity");
        } catch (error) {
            this.showToast(error.message, "error");
            return;
        }

        try {
            this.setActionLoading(true);
            await window.SecondMarketAdminAPI.updateProductInventory(productSlug, quantity);
            this.showToast("Product inventory updated.");
            await this.refreshInventory();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    async createCategory(event) {
        event.preventDefault();
        if (this.state.actionLoading) return;

        const form = new FormData(event.currentTarget);
        let payload;

        try {
            payload = {
                name: (form.get("name") || "").toString().trim(),
                slug: (form.get("slug") || "").toString().trim(),
                description: (form.get("description") || "").toString().trim(),
                sort_order: this.parseNonNegativeInteger(form.get("sort_order") || "0", "Sort order"),
                is_active: true,
            };
        } catch (error) {
            this.showToast(error.message, "error");
            return;
        }

        try {
            this.setActionLoading(true);
            await window.SecondMarketAdminAPI.createCategory(payload);
            event.currentTarget.reset();
            this.showToast("Category created.");
            await this.refreshInventory();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    async setCategoryStatus(categorySlug, isActiveValue) {
        if (this.state.actionLoading) return;

        try {
            this.setActionLoading(true);
            await window.SecondMarketAdminAPI.updateCategoryStatus(categorySlug, isActiveValue === "true");
            this.showToast("Category status updated.");
            await this.refreshInventory();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    async setCategorySortOrder(event, categorySlug) {
        event.preventDefault();
        if (this.state.actionLoading) return;

        const form = new FormData(event.currentTarget);
        let sortOrder;

        try {
            sortOrder = this.parseNonNegativeInteger(form.get("sort_order") || "0", "Sort order");
        } catch (error) {
            this.showToast(error.message, "error");
            return;
        }

        try {
            this.setActionLoading(true);
            await window.SecondMarketAdminAPI.updateCategory(categorySlug, { sort_order: sortOrder });
            this.showToast("Category sort order updated.");
            await this.refreshInventory();
        } catch (error) {
            this.showToast(window.SecondMarketAdminAPI.formatError(error), "error");
        } finally {
            this.setActionLoading(false);
        }
    }

    navigate(viewName) {
        this.state.currentView = viewName;
        if (viewName !== "orders") {
            this.state.currentOrder = null;
        }
        this.render();
        document.getElementById("admin-main-content")?.focus();
    }

    async logout() {
        try {
            await window.SecondMarketAuthAPI.logout();
        } finally {
            window.location.href = "/admin/login.html";
        }
    }

    loadPageTemplate(templateName) {
        if (this.templateCache[templateName]) {
            return this.templateCache[templateName];
        }

        const request = new XMLHttpRequest();
        request.open("GET", `/admin/pages/${templateName}.html`, false);
        request.send(null);

        if (request.status < 200 || request.status >= 300) {
            return `
                <section class="admin-state-panel">
                    <h2>Page Template Missing</h2>
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

    renderInventoryStatus(message) {
        if (this.state.loading) {
            return `<div class="admin-state-panel"><h2>Loading</h2><p>${this.escapeHtml(message)}</p></div>`;
        }

        if (this.state.error) {
            return `<div class="admin-state-panel"><h2>Unable to load data</h2><p>${this.escapeHtml(this.state.error)}</p></div>`;
        }

        return "";
    }

    render() {
        const main = document.getElementById("admin-main-content");
        if (!main) return;

        this.updateUserDisplay();
        this.updateNavigation();

        if (!this.state.user) {
            main.innerHTML = this.renderAccessPanel(
                "Admin Sign In Required",
                "Sign in with an admin seller account to manage SecondMarket inventory.",
                "/admin/login.html",
                "Go To Sign In"
            );
            return;
        }

        if (this.state.user.role !== "admin") {
            main.innerHTML = this.renderAccessPanel(
                "Admin Access Required",
                "Your current account does not have permission to manage seller inventory.",
                "/",
                "Back To Storefront"
            );
            return;
        }

        if (this.state.currentView === "products") {
            document.getElementById("admin-page-title").textContent = "Product Listings";
            main.innerHTML = window.SecondMarketAdminPages.renderProductsPage.call(this);
            return;
        }

        if (this.state.currentView === "categories") {
            document.getElementById("admin-page-title").textContent = "Categories";
            main.innerHTML = window.SecondMarketAdminPages.renderCategoriesPage.call(this);
            return;
        }

        if (this.state.currentView === "orders") {
            document.getElementById("admin-page-title").textContent = "Orders";
            main.innerHTML = window.SecondMarketAdminPages.renderOrdersPage.call(this);
            return;
        }

        document.getElementById("admin-page-title").textContent = "Inventory Dashboard";
        main.innerHTML = window.SecondMarketAdminPages.renderDashboardPage.call(this);
    }

    renderAccessPanel(title, message, href, actionText) {
        return `
            <section class="admin-state-panel" aria-live="polite">
                <h2>${this.escapeHtml(title)}</h2>
                <p>${this.escapeHtml(message)}</p>
                <a href="${href}" class="admin-button-primary">${this.escapeHtml(actionText)}</a>
            </section>
        `;
    }

    updateUserDisplay() {
        const label = document.querySelector("[data-admin-user-name]");
        if (!label) return;
        label.textContent = this.state.user
            ? `${this.state.user.first_name} ${this.state.user.last_name} (${this.state.user.role})`
            : "Not signed in";
    }

    updateNavigation() {
        document.querySelectorAll("[data-admin-nav]").forEach((button) => {
            button.classList.toggle("is-active", button.dataset.adminNav === this.state.currentView);
        });
    }

    productCell(product) {
        const imageUrl = product.primary_image?.url || "/static/productImages/bags/young-girl-with-gray-student-backpack.jpg";
        const imageAlt = product.primary_image?.alt_text || product.title;
        return `
            <div class="admin-product-cell">
                <img src="${this.escapeAttribute(imageUrl)}" alt="${this.escapeAttribute(imageAlt)}" class="admin-product-thumb">
                <div>
                    <strong>${this.escapeHtml(product.title)}</strong>
                    <div class="admin-muted">${this.escapeHtml(product.slug)}</div>
                </div>
            </div>
        `;
    }

    statusBadge(status, label = null) {
        return `<span class="admin-badge ${this.escapeAttribute(status)}">${this.escapeHtml(label || status)}</span>`;
    }

    conditionLabel(condition) {
        const labels = {
            new_other: "New Other",
            like_new: "Like New",
            good: "Good",
            fair: "Fair",
            for_repair: "For Repair",
        };
        return labels[condition] || "Secondhand";
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

    emptyTableRow(message, colspan) {
        return `<tr><td colspan="${colspan}" class="admin-empty-row">${this.escapeHtml(message)}</td></tr>`;
    }

    showToast(message, type = "success") {
        const container = document.getElementById("admin-toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `admin-toast ${type === "error" ? "is-error" : ""}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
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

let adminApp;
window.addEventListener("DOMContentLoaded", () => {
    adminApp = new SecondMarketAdminApp();
});
