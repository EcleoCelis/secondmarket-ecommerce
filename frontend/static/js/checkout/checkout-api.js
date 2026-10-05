(function () {
    const BASE_URL = "/api/v1/cart";
    const CHECKOUT_BASE_URL = "/api/v1/checkout";

    async function request(path = "", options = {}, baseUrl = BASE_URL) {
        const response = await fetch(`${baseUrl}${path}`, {
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
            const error = new Error(payload.message || "Cart request failed.");
            error.status = response.status;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    async function getCart() {
        const payload = await request("");
        return payload.data;
    }

    async function addItem(productSlug, quantity = 1) {
        const payload = await request("/items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_slug: productSlug, quantity }),
        });
        return payload.data;
    }

    async function updateItem(productSlug, quantity) {
        const payload = await request(`/items/${encodeURIComponent(productSlug)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity }),
        });
        return payload.data;
    }

    async function removeItem(productSlug) {
        const payload = await request(`/items/${encodeURIComponent(productSlug)}`, {
            method: "DELETE",
        });
        return payload.data;
    }

    async function createDraft(checkoutData) {
        const payload = await request("/draft", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(checkoutData),
        }, CHECKOUT_BASE_URL);
        return payload.data;
    }

    async function confirmOrder(checkoutData) {
        const payload = await request("/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(checkoutData),
        }, CHECKOUT_BASE_URL);
        return payload.data;
    }

    function formatError(error) {
        const details = error?.payload?.error?.details || {};
        const messages = Object.values(details).flat().filter(Boolean);
        return messages.length ? messages.join(" ") : error.message || "The checkout workspace is temporarily unavailable.";
    }

    window.SecondMarketCheckoutAPI = {
        addItem,
        confirmOrder,
        createDraft,
        formatError,
        getCart,
        removeItem,
        updateItem,
    };
})();
