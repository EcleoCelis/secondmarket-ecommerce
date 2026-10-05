(function () {
    const BASE_URL = "/api/v1/admin";

    async function request(path, options = {}) {
        const response = await fetch(`${BASE_URL}${path}`, {
            credentials: "include",
            headers: {
                Accept: "application/json",
                ...(options.headers || {}),
            },
            ...options,
        });
        const payload = await response.json().catch(() => ({
            success: false,
            message: "The server returned an unreadable response.",
            error: { details: {} },
        }));

        if (!response.ok || payload.success === false) {
            const error = new Error(payload.message || "Admin request failed.");
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    function buildQueryString(params = {}) {
        const query = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value === undefined || value === null || value === "" || value === "all") return;
            query.set(key, value);
        });

        const queryString = query.toString();
        return queryString ? `?${queryString}` : "";
    }

    async function listCategories() {
        const payload = await request("/categories");
        return payload.data;
    }

    async function createCategory(data) {
        const payload = await request("/categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return payload.data;
    }

    async function updateCategory(categorySlug, data) {
        const payload = await request(`/categories/${encodeURIComponent(categorySlug)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return payload.data;
    }

    async function updateCategoryStatus(categorySlug, isActive) {
        const payload = await request(`/categories/${encodeURIComponent(categorySlug)}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: isActive }),
        });
        return payload.data;
    }

    async function listProducts(filters = {}) {
        const payload = await request(`/products${buildQueryString(filters)}`);
        return {
            products: payload.data,
            count: payload.meta?.count || payload.data.length,
        };
    }

    async function listOrders(filters = {}) {
        const payload = await request(`/orders${buildQueryString(filters)}`);
        return {
            orders: payload.data,
            count: payload.meta?.count || payload.data.length,
        };
    }

    async function getOrder(orderNumber) {
        const payload = await request(`/orders/${encodeURIComponent(orderNumber)}`);
        return payload.data;
    }

    async function updateProductStatus(productSlug, status) {
        const payload = await request(`/products/${encodeURIComponent(productSlug)}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        return payload.data;
    }

    async function updateProductInventory(productSlug, quantity) {
        const payload = await request(`/products/${encodeURIComponent(productSlug)}/inventory`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity }),
        });
        return payload.data;
    }

    function formatError(error) {
        const details = error?.payload?.error?.details || {};
        const messages = Object.values(details).flat().filter(Boolean);
        return messages.length ? messages.join(" ") : error.message || "The admin workspace is temporarily unavailable.";
    }

    window.SecondMarketAdminAPI = {
        buildQueryString,
        createCategory,
        formatError,
        getOrder,
        listCategories,
        listOrders,
        listProducts,
        updateCategory,
        updateCategoryStatus,
        updateProductInventory,
        updateProductStatus,
    };
})();
